#include "vectors.hpp"
#include <opencv2/opencv.hpp>
#include <cmath>
#include <algorithm>
#include <vector>
#include <random>

static cv::Mat to_mat_gray(py::array_t<uint8_t>& arr) {
    auto buf = arr.request();
    return cv::Mat(static_cast<int>(buf.shape[0]),
                   static_cast<int>(buf.shape[1]), CV_8UC1, buf.ptr);
}

static cv::Mat maybe_downsample(const cv::Mat& img, int max_dim = 2000) {
    int h = img.rows, w = img.cols;
    if (std::max(h, w) <= max_dim) return img;
    double scale = static_cast<double>(max_dim) / std::max(h, w);
    cv::Mat small;
    cv::resize(img, small, cv::Size(), scale, scale, cv::INTER_AREA);
    return small;
}

py::list detect_vectors(
    py::array_t<uint8_t> img_gray,
    double rho,
    double theta,
    int threshold,
    double min_line_length,
    double max_line_gap)
{
    cv::Mat gray = to_mat_gray(img_gray);
    int orig_h = gray.rows, orig_w = gray.cols;
    double scale = 1.0;

    cv::Mat proc = maybe_downsample(gray);
    if (proc.rows != orig_h) {
        scale = static_cast<double>(proc.rows) / orig_h;
    }

    // Canny edge detection
    cv::Mat edges;
    cv::Canny(proc, edges, 50, 150, 3);

    // Probabilistic Hough Line Transform
    std::vector<cv::Vec4i> lines;
    cv::HoughLinesP(edges, lines, rho, theta,
                    static_cast<int>(threshold * scale),
                    min_line_length * scale,
                    max_line_gap * scale);

    py::list result;
    for (auto& l : lines) {
        double x1 = l[0] / scale;
        double y1 = l[1] / scale;
        double x2 = l[2] / scale;
        double y2 = l[3] / scale;

        // Normalise coordinates to [0, 1]
        double nx1 = x1 / orig_w, ny1 = y1 / orig_h;
        double nx2 = x2 / orig_w, ny2 = y2 / orig_h;

        // Compute angle in degrees [0, 180)
        double dx = x2 - x1, dy = y2 - y1;
        double angle = std::atan2(std::abs(dy), std::abs(dx)) * 180.0 / M_PI;

        // Line strength = length
        double strength = std::sqrt(dx * dx + dy * dy) / std::sqrt(
            static_cast<double>(orig_w * orig_w + orig_h * orig_h));

        // Classify direction
        std::string direction;
        if (angle < 15.0 || angle > 165.0)
            direction = "horizontal";
        else if (angle > 75.0 && angle < 105.0)
            direction = "vertical";
        else
            direction = "diagonal";

        py::dict vec;
        vec["x1"] = nx1;
        vec["y1"] = ny1;
        vec["x2"] = nx2;
        vec["y2"] = ny2;
        vec["angle"] = angle;
        vec["strength"] = strength;
        vec["direction"] = direction;
        result.append(vec);
    }

    return result;
}

py::dict estimate_vanishing_point(
    py::array_t<uint8_t> img_gray)
{
    // RANSAC vanishing point estimation
    cv::Mat gray = to_mat_gray(img_gray);
    cv::Mat proc = maybe_downsample(gray);
    double scale = static_cast<double>(proc.rows) / gray.rows;
    int h = gray.rows, w = gray.cols;

    // Detect edges and lines
    cv::Mat edges;
    cv::Canny(proc, edges, 50, 150, 3);
    std::vector<cv::Vec4i> lines;
    cv::HoughLinesP(edges, lines, 1.0, CV_PI / 180, 80,
                    std::max(30.0, proc.cols * 0.05), 10.0);

    py::dict result;

    if (lines.size() < 4) {
        result["vp_x"] = py::none();
        result["vp_y"] = py::none();
        result["v_angle"] = 0.0;
        result["h_angle"] = 0.0;
        return result;
    }

    // Convert lines to line equations (a, b, c) where ax + by + c = 0
    struct Line2D {
        double a, b, c;
        double x1, y1, x2, y2;
    };
    std::vector<Line2D> line_eqs;
    for (auto& l : lines) {
        double lx1 = l[0] / scale, ly1 = l[1] / scale;
        double lx2 = l[2] / scale, ly2 = l[3] / scale;
        double a = ly2 - ly1;
        double b = lx1 - lx2;
        double c = lx2 * ly1 - lx1 * ly2;
        double norm = std::sqrt(a * a + b * b);
        if (norm < 1e-10) continue;
        line_eqs.push_back({a / norm, b / norm, c / norm, lx1, ly1, lx2, ly2});
    }

    if (line_eqs.size() < 4) {
        result["vp_x"] = py::none();
        result["vp_y"] = py::none();
        result["v_angle"] = 0.0;
        result["h_angle"] = 0.0;
        return result;
    }

    // Filter out near-horizontal and near-vertical lines (keep diagonals + perspective lines)
    std::vector<Line2D> perspective_lines;
    for (auto& le : line_eqs) {
        double angle = std::atan2(std::abs(le.y2 - le.y1), std::abs(le.x2 - le.x1)) * 180.0 / M_PI;
        if (angle > 10.0 && angle < 80.0) {
            perspective_lines.push_back(le);
        }
    }

    if (perspective_lines.size() < 2) {
        result["vp_x"] = py::none();
        result["vp_y"] = py::none();
        result["v_angle"] = 0.0;
        result["h_angle"] = 0.0;
        return result;
    }

    // RANSAC: find intersection with most inliers
    std::mt19937 rng(42);
    int max_inliers = 0;
    double best_x = w / 2.0, best_y = h / 2.0;
    double inlier_thresh = std::max(h, w) * 0.05;
    int n_iter = std::min(500, static_cast<int>(perspective_lines.size() * perspective_lines.size()));

    for (int iter = 0; iter < n_iter; ++iter) {
        int i = rng() % perspective_lines.size();
        int j = rng() % perspective_lines.size();
        if (i == j) continue;

        auto& l1 = perspective_lines[i];
        auto& l2 = perspective_lines[j];

        // Compute intersection
        double det = l1.a * l2.b - l2.a * l1.b;
        if (std::abs(det) < 1e-10) continue;

        double ix = (l1.b * l2.c - l2.b * l1.c) / det;
        double iy = (l2.a * l1.c - l1.a * l2.c) / det;

        // Skip if intersection is too far from image
        if (std::abs(ix) > w * 3 || std::abs(iy) > h * 3) continue;

        // Count inliers
        int inliers = 0;
        for (auto& le : perspective_lines) {
            double dist = std::abs(le.a * ix + le.b * iy + le.c);
            if (dist < inlier_thresh) inliers++;
        }

        if (inliers > max_inliers) {
            max_inliers = inliers;
            best_x = ix;
            best_y = iy;
        }
    }

    if (max_inliers < 3) {
        result["vp_x"] = py::none();
        result["vp_y"] = py::none();
        result["v_angle"] = 0.0;
        result["h_angle"] = 0.0;
        return result;
    }

    // Compute angles from VP position relative to image centre
    double cx = w / 2.0, cy = h / 2.0;
    double v_angle = std::atan2(cy - best_y, w) * 180.0 / M_PI;
    double h_angle = std::atan2(best_x - cx, h) * 180.0 / M_PI;

    result["vp_x"] = best_x / w;   // normalised
    result["vp_y"] = best_y / h;
    result["v_angle"] = v_angle;
    result["h_angle"] = h_angle;
    return result;
}

py::dict detect_framing_lines(
    py::array_t<uint8_t> img_gray,
    double threshold1,
    double threshold2)
{
    // Framing detection (Kress & vL, pp.203-204)
    cv::Mat gray = to_mat_gray(img_gray);
    cv::Mat proc = maybe_downsample(gray);
    double scale = static_cast<double>(proc.rows) / gray.rows;
    int h = gray.rows, w = gray.cols;

    cv::Mat edges;
    cv::Canny(proc, edges, threshold1, threshold2, 3);

    // Detect strong lines
    std::vector<cv::Vec4i> lines;
    cv::HoughLinesP(edges, lines, 1.0, CV_PI / 180, 80,
                    std::max(50.0, proc.cols * 0.15), 10.0);

    py::list frame_lines;
    int h_frame_count = 0, v_frame_count = 0;

    for (auto& l : lines) {
        double x1 = l[0] / scale, y1 = l[1] / scale;
        double x2 = l[2] / scale, y2 = l[3] / scale;
        double dx = x2 - x1, dy = y2 - y1;
        double angle = std::atan2(std::abs(dy), std::abs(dx)) * 180.0 / M_PI;
        double length = std::sqrt(dx * dx + dy * dy);

        bool is_framing = false;

        // Horizontal framing lines: span significant width
        if (angle < 10.0 && length > w * 0.3) {
            h_frame_count++;
            is_framing = true;
        }
        // Vertical framing lines: span significant height
        if (angle > 80.0 && length > h * 0.3) {
            v_frame_count++;
            is_framing = true;
        }

        if (is_framing) {
            py::dict fl;
            fl["x1"] = x1 / w;
            fl["y1"] = y1 / h;
            fl["x2"] = x2 / w;
            fl["y2"] = y2 / h;
            fl["orientation"] = (angle < 10.0) ? "horizontal" : "vertical";
            fl["length"] = length / std::sqrt(static_cast<double>(w * w + h * h));
            frame_lines.append(fl);
        }
    }

    // Framing score: how much the image is divided by frame lines
    double max_possible = 6.0;  // reasonable max for frame lines
    double framing_score = std::min(1.0,
        static_cast<double>(h_frame_count + v_frame_count) / max_possible);

    py::dict result;
    result["framing_score"] = framing_score;
    result["lines"] = frame_lines;
    return result;
}
