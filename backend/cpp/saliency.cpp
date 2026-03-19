#include "saliency.hpp"
#include <opencv2/opencv.hpp>
#include <cmath>
#include <algorithm>
#include <vector>

// Helper: numpy RGB -> cv::Mat (zero-copy)
static cv::Mat to_mat_rgb(py::array_t<uint8_t>& arr) {
    auto buf = arr.request();
    return cv::Mat(static_cast<int>(buf.shape[0]),
                   static_cast<int>(buf.shape[1]), CV_8UC3, buf.ptr);
}

static cv::Mat to_mat_float(py::array_t<float>& arr) {
    auto buf = arr.request();
    return cv::Mat(static_cast<int>(buf.shape[0]),
                   static_cast<int>(buf.shape[1]), CV_32FC1, buf.ptr);
}

static py::array_t<float> mat_to_numpy(const cv::Mat& src) {
    cv::Mat mat;
    if (src.type() != CV_32FC1)
        src.convertTo(mat, CV_32FC1);
    else
        mat = src;
    if (!mat.isContinuous())
        mat = mat.clone();
    auto result = py::array_t<float>({mat.rows, mat.cols});
    std::memcpy(result.mutable_data(), mat.data,
                static_cast<size_t>(mat.rows) * mat.cols * sizeof(float));
    return result;
}

// Auto-downsample if image is too large
static cv::Mat maybe_downsample(const cv::Mat& img, int max_dim = 2000) {
    int h = img.rows, w = img.cols;
    if (std::max(h, w) <= max_dim) return img;
    double scale = static_cast<double>(max_dim) / std::max(h, w);
    cv::Mat small;
    cv::resize(img, small, cv::Size(), scale, scale, cv::INTER_AREA);
    return small;
}

py::array_t<float> compute_saliency_spectral(
    py::array_t<uint8_t> img_rgb,
    double scale_factor)
{
    // Spectral Residual saliency (Hou & Zhang, 2007)
    cv::Mat rgb = to_mat_rgb(img_rgb);
    cv::Mat small = maybe_downsample(rgb);
    int orig_h = rgb.rows, orig_w = rgb.cols;

    // Convert to grayscale float
    cv::Mat gray;
    cv::cvtColor(small, gray, cv::COLOR_RGB2GRAY);
    gray.convertTo(gray, CV_32F, 1.0 / 255.0);

    if (scale_factor != 1.0 && scale_factor > 0) {
        cv::resize(gray, gray, cv::Size(), scale_factor, scale_factor, cv::INTER_AREA);
    }

    // Optimal DFT size
    int h = cv::getOptimalDFTSize(gray.rows);
    int w = cv::getOptimalDFTSize(gray.cols);
    cv::Mat padded;
    cv::copyMakeBorder(gray, padded, 0, h - gray.rows, 0, w - gray.cols,
                       cv::BORDER_CONSTANT, cv::Scalar(0));

    // DFT
    cv::Mat planes[] = {padded, cv::Mat::zeros(padded.size(), CV_32F)};
    cv::Mat complex_img;
    cv::merge(planes, 2, complex_img);
    cv::dft(complex_img, complex_img);
    cv::split(complex_img, planes);

    // Log amplitude spectrum
    cv::Mat magnitude, phase;
    cv::cartToPolar(planes[0], planes[1], magnitude, phase);
    cv::Mat log_amp;
    cv::log(magnitude + 1e-10, log_amp);

    // Spectral residual = log_amplitude - average_filtered(log_amplitude)
    cv::Mat avg_log_amp;
    cv::blur(log_amp, avg_log_amp, cv::Size(3, 3));
    cv::Mat spectral_residual = log_amp - avg_log_amp;

    // Reconstruct via inverse DFT
    cv::Mat exp_sr;
    cv::exp(spectral_residual, exp_sr);
    cv::Mat re, im;
    cv::polarToCart(exp_sr, phase, re, im);
    cv::Mat inv_planes[] = {re, im};
    cv::Mat inv_complex;
    cv::merge(inv_planes, 2, inv_complex);
    cv::Mat inv_out;
    cv::idft(inv_complex, inv_out);

    // Get magnitude of complex output
    cv::Mat inv_split[2];
    cv::split(inv_out, inv_split);
    cv::Mat saliency;
    cv::magnitude(inv_split[0], inv_split[1], saliency);

    // Square and blur to get saliency
    cv::multiply(saliency, saliency, saliency);
    cv::GaussianBlur(saliency, saliency, cv::Size(7, 7), 2.5);

    // Crop back to original padded size
    saliency = saliency(cv::Rect(0, 0, gray.cols, gray.rows));

    // Resize to original image dimensions
    cv::resize(saliency, saliency, cv::Size(orig_w, orig_h), 0, 0, cv::INTER_LINEAR);

    // Normalise to [0, 1]
    double minv, maxv;
    cv::minMaxLoc(saliency, &minv, &maxv);
    cv::Mat result_mat;
    if (maxv - minv > 1e-10) {
        result_mat = (saliency - minv) / (maxv - minv);
    } else {
        result_mat = cv::Mat::zeros(saliency.size(), CV_32F);
    }

    // Ensure continuous memory layout for numpy
    if (!result_mat.isContinuous())
        result_mat = result_mat.clone();

    return mat_to_numpy(result_mat);
}

py::array_t<float> compute_saliency_itti(
    py::array_t<uint8_t> img_rgb,
    double scale_factor)
{
    // Simplified Itti-Koch saliency using intensity, colour, and orientation
    cv::Mat rgb = to_mat_rgb(img_rgb);
    cv::Mat small = maybe_downsample(rgb);
    int orig_h = rgb.rows, orig_w = rgb.cols;

    if (scale_factor != 1.0 && scale_factor > 0) {
        cv::resize(small, small, cv::Size(), scale_factor, scale_factor, cv::INTER_AREA);
    }

    cv::Mat fimg;
    small.convertTo(fimg, CV_32F, 1.0 / 255.0);

    // Split channels
    std::vector<cv::Mat> channels(3);
    cv::split(fimg, channels);
    cv::Mat R = channels[0], G = channels[1], B = channels[2];

    // Intensity channel
    cv::Mat intensity = (R + G + B) / 3.0;

    // Colour opponency channels
    cv::Mat RG = R - G;
    cv::Mat BY = (R + G) / 2.0 - B;

    // Build Gaussian pyramid (6 levels)
    auto build_pyramid = [](const cv::Mat& src, int levels) {
        std::vector<cv::Mat> pyr;
        pyr.push_back(src.clone());
        for (int i = 1; i < levels; ++i) {
            cv::Mat down;
            cv::pyrDown(pyr.back(), down);
            pyr.push_back(down);
        }
        return pyr;
    };

    int n_levels = 6;
    auto pyr_I = build_pyramid(intensity, n_levels);
    auto pyr_RG = build_pyramid(RG, n_levels);
    auto pyr_BY = build_pyramid(BY, n_levels);

    // Centre-surround differences
    auto centre_surround = [](const std::vector<cv::Mat>& pyr, int c, int s) {
        cv::Mat fine = pyr[c];
        cv::Mat coarse;
        cv::resize(pyr[s], coarse, fine.size(), 0, 0, cv::INTER_LINEAR);
        cv::Mat diff;
        cv::absdiff(fine, coarse, diff);
        return diff;
    };

    cv::Mat conspicuity_I = cv::Mat::zeros(intensity.size(), CV_32F);
    cv::Mat conspicuity_C = cv::Mat::zeros(intensity.size(), CV_32F);

    // Centre-surround pairs: c in {1,2}, s in {c+2, c+3}
    for (int c = 1; c <= 2; ++c) {
        for (int delta = 2; delta <= 3; ++delta) {
            int s = c + delta;
            if (s >= n_levels) continue;

            cv::Mat cs_I = centre_surround(pyr_I, c, s);
            cv::resize(cs_I, cs_I, intensity.size(), 0, 0, cv::INTER_LINEAR);
            conspicuity_I += cs_I;

            cv::Mat cs_RG = centre_surround(pyr_RG, c, s);
            cv::Mat cs_BY = centre_surround(pyr_BY, c, s);
            cv::resize(cs_RG, cs_RG, intensity.size(), 0, 0, cv::INTER_LINEAR);
            cv::resize(cs_BY, cs_BY, intensity.size(), 0, 0, cv::INTER_LINEAR);
            conspicuity_C += cs_RG + cs_BY;
        }
    }

    // Orientation conspicuity via Gabor filters at 4 orientations
    cv::Mat gray;
    cv::cvtColor(small, gray, cv::COLOR_RGB2GRAY);
    gray.convertTo(gray, CV_32F, 1.0 / 255.0);

    cv::Mat conspicuity_O = cv::Mat::zeros(gray.size(), CV_32F);
    double orientations[] = {0, M_PI / 4, M_PI / 2, 3 * M_PI / 4};
    for (double theta : orientations) {
        cv::Mat kernel = cv::getGaborKernel(cv::Size(31, 31), 4.0, theta, 10.0, 0.5, 0, CV_32F);
        cv::Mat response;
        cv::filter2D(gray, response, CV_32F, kernel);
        conspicuity_O += cv::abs(response);
    }

    // Normalise each conspicuity map
    auto normalise_map = [](cv::Mat& m) {
        double minv, maxv;
        cv::minMaxLoc(m, &minv, &maxv);
        if (maxv - minv > 1e-10)
            m = (m - minv) / (maxv - minv);
        else
            m = cv::Mat::zeros(m.size(), CV_32F);
    };

    normalise_map(conspicuity_I);
    normalise_map(conspicuity_C);
    normalise_map(conspicuity_O);

    // Combine with equal weights
    cv::Mat saliency = (conspicuity_I + conspicuity_C + conspicuity_O) / 3.0;
    cv::GaussianBlur(saliency, saliency, cv::Size(7, 7), 2.5);

    // Resize to original dimensions
    cv::resize(saliency, saliency, cv::Size(orig_w, orig_h), 0, 0, cv::INTER_LINEAR);

    normalise_map(saliency);

    return mat_to_numpy(saliency);
}

py::list compute_reading_path(
    py::array_t<float> saliency_map,
    int max_waypoints)
{
    // Extract reading path from saliency peaks (Kress & vL, pp.204-208)
    cv::Mat sal = to_mat_float(saliency_map);
    int h = sal.rows, w = sal.cols;

    // Non-maximum suppression with a local window
    int win = std::max(15, std::min(h, w) / 20);
    if (win % 2 == 0) win++;

    cv::Mat dilated;
    cv::dilate(sal, dilated, cv::getStructuringElement(cv::MORPH_RECT, cv::Size(win, win)));

    // Find peaks: pixels that are local maxima and above a threshold
    double minv, maxv;
    cv::minMaxLoc(sal, &minv, &maxv);
    double threshold = minv + (maxv - minv) * 0.2;

    struct Peak {
        int x, y;
        float val;
    };
    std::vector<Peak> peaks;

    for (int r = win / 2; r < h - win / 2; r += win / 2) {
        for (int c = win / 2; c < w - win / 2; c += win / 2) {
            float v = sal.at<float>(r, c);
            if (v >= threshold && std::abs(v - dilated.at<float>(r, c)) < 1e-6) {
                peaks.push_back({c, r, v});
            }
        }
    }

    // Sort by saliency descending
    std::sort(peaks.begin(), peaks.end(),
              [](const Peak& a, const Peak& b) { return a.val > b.val; });

    // Remove peaks too close to each other
    int min_dist = std::max(h, w) / 10;
    std::vector<Peak> filtered;
    for (auto& p : peaks) {
        bool too_close = false;
        for (auto& f : filtered) {
            int dx = p.x - f.x, dy = p.y - f.y;
            if (dx * dx + dy * dy < min_dist * min_dist) {
                too_close = true;
                break;
            }
        }
        if (!too_close) {
            filtered.push_back(p);
            if (static_cast<int>(filtered.size()) >= max_waypoints) break;
        }
    }

    // Order by nearest-neighbour traversal starting from the most salient
    std::vector<Peak> ordered;
    if (!filtered.empty()) {
        std::vector<bool> used(filtered.size(), false);
        int cur = 0;
        used[0] = true;
        ordered.push_back(filtered[0]);

        for (size_t i = 1; i < filtered.size(); ++i) {
            int best = -1;
            double best_dist = 1e18;
            for (size_t j = 0; j < filtered.size(); ++j) {
                if (used[j]) continue;
                double dx = filtered[j].x - filtered[cur].x;
                double dy = filtered[j].y - filtered[cur].y;
                double d = dx * dx + dy * dy;
                if (d < best_dist) {
                    best_dist = d;
                    best = static_cast<int>(j);
                }
            }
            if (best >= 0) {
                used[best] = true;
                ordered.push_back(filtered[best]);
                cur = best;
            }
        }
    }

    // Classify path shape
    auto classify_shape = [&](const std::vector<Peak>& pts, int img_w, int img_h) -> std::string {
        if (pts.size() < 3) return "irregular";

        // Check if mostly left-to-right
        int lr_increases = 0;
        for (size_t i = 1; i < pts.size(); ++i)
            if (pts[i].x > pts[i - 1].x) lr_increases++;

        // Check if mostly top-to-bottom
        int tb_increases = 0;
        for (size_t i = 1; i < pts.size(); ++i)
            if (pts[i].y > pts[i - 1].y) tb_increases++;

        double lr_ratio = static_cast<double>(lr_increases) / (pts.size() - 1);
        double tb_ratio = static_cast<double>(tb_increases) / (pts.size() - 1);

        // Check Z-pattern: alternating left-right movement with downward trend
        int direction_changes = 0;
        for (size_t i = 2; i < pts.size(); ++i) {
            bool prev_right = pts[i - 1].x > pts[i - 2].x;
            bool cur_right = pts[i].x > pts[i - 1].x;
            if (prev_right != cur_right) direction_changes++;
        }

        if (lr_ratio > 0.75 && tb_ratio < 0.4) return "linear_lr";
        if (tb_ratio > 0.75 && lr_ratio < 0.4) return "linear_tb";
        if (direction_changes >= 2 && tb_ratio > 0.5) return "z_pattern";

        // Check circular: first and last points are close
        if (pts.size() >= 4) {
            double dx = pts.front().x - pts.back().x;
            double dy = pts.front().y - pts.back().y;
            double loop_dist = std::sqrt(dx * dx + dy * dy);
            double diag = std::sqrt(static_cast<double>(img_w * img_w + img_h * img_h));
            if (loop_dist < diag * 0.2) return "circular";
        }

        return "irregular";
    };

    // Build result list
    py::list result;
    for (size_t i = 0; i < ordered.size(); ++i) {
        py::dict wp;
        wp["x"] = static_cast<double>(ordered[i].x) / w;
        wp["y"] = static_cast<double>(ordered[i].y) / h;
        wp["saliency"] = static_cast<double>(ordered[i].val);
        wp["label"] = "waypoint_" + std::to_string(i + 1);
        result.append(wp);
    }

    return result;
}
