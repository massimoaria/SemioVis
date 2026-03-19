#include "spatial_grid.hpp"
#include <opencv2/opencv.hpp>
#include <string>
#include <cmath>

static cv::Mat to_mat_float(py::array_t<float>& arr) {
    auto buf = arr.request();
    return cv::Mat(static_cast<int>(buf.shape[0]),
                   static_cast<int>(buf.shape[1]), CV_32FC1, buf.ptr);
}

static cv::Mat to_mat_rgb(py::array_t<uint8_t>& arr) {
    auto buf = arr.request();
    return cv::Mat(static_cast<int>(buf.shape[0]),
                   static_cast<int>(buf.shape[1]), CV_8UC3, buf.ptr);
}

py::list compute_spatial_zones(
    py::array_t<float> saliency_map,
    py::array_t<uint8_t> img_rgb,
    int n_cols,
    int n_rows)
{
    cv::Mat sal = to_mat_float(saliency_map);
    cv::Mat rgb = to_mat_rgb(img_rgb);
    int h = rgb.rows, w = rgb.cols;

    // Compute global stats for contrast calculation
    cv::Mat gray;
    cv::cvtColor(rgb, gray, cv::COLOR_RGB2GRAY);
    double global_mean_brightness = cv::mean(gray)[0];

    // Convert to HSV for colour analysis
    cv::Mat hsv;
    cv::cvtColor(rgb, hsv, cv::COLOR_RGB2HSV);

    py::list zones;

    for (int r = 0; r < n_rows; ++r) {
        for (int c = 0; c < n_cols; ++c) {
            int y1 = r * h / n_rows;
            int y2 = (r + 1) * h / n_rows;
            int x1 = c * w / n_cols;
            int x2 = (c + 1) * w / n_cols;

            cv::Rect roi(x1, y1, x2 - x1, y2 - y1);
            cv::Mat zone_rgb = rgb(roi);
            cv::Mat zone_sal = sal(roi);
            cv::Mat zone_gray = gray(roi);
            cv::Mat zone_hsv = hsv(roi);

            // Mean saliency
            double mean_sal = cv::mean(zone_sal)[0];

            // Edge density (Canny)
            cv::Mat zone_edges;
            cv::Canny(zone_gray, zone_edges, 50, 150);
            double edge_density = cv::countNonZero(zone_edges) /
                static_cast<double>(zone_edges.rows * zone_edges.cols);

            // Tonal contrast: difference between zone and global mean brightness
            double zone_mean_brightness = cv::mean(zone_gray)[0];
            double tonal_contrast = std::abs(zone_mean_brightness - global_mean_brightness) / 255.0;

            // Colour contrast: std dev of hue in the zone
            std::vector<cv::Mat> hsv_channels;
            cv::split(zone_hsv, hsv_channels);
            cv::Scalar hue_mean, hue_std;
            cv::meanStdDev(hsv_channels[0], hue_mean, hue_std);
            double colour_contrast = std::min(1.0, hue_std[0] / 90.0);

            // Sharpness: Laplacian variance
            cv::Mat laplacian;
            cv::Laplacian(zone_gray, laplacian, CV_64F);
            cv::Scalar lap_mean, lap_std;
            cv::meanStdDev(laplacian, lap_mean, lap_std);
            double sharpness = std::min(1.0, lap_std[0] * lap_std[0] / 1000.0);

            // Colour temperature from average hue
            double avg_hue = hue_mean[0];  // 0-180 in OpenCV HSV
            double avg_sat = cv::mean(hsv_channels[1])[0] / 255.0;
            std::string color_temp;
            if (avg_sat < 0.15) {
                color_temp = "neutral";
            } else if (avg_hue < 30 || avg_hue > 160) {
                color_temp = "warm";   // reds, oranges, yellows
            } else if (avg_hue > 80 && avg_hue < 140) {
                color_temp = "cool";   // blues, greens
            } else {
                color_temp = "neutral";
            }

            // Visual weight: combination of saliency, edge density, contrast
            double visual_weight = 0.5 * mean_sal + 0.2 * edge_density +
                                   0.15 * tonal_contrast + 0.15 * sharpness;

            // Information value score
            double info_score = visual_weight;

            // Position label
            std::string v_pos = (r == 0) ? "top" : (r == n_rows - 1) ? "bottom" : "center";
            std::string h_pos = (c == 0) ? "left" : (c == n_cols - 1) ? "right" : "center";
            std::string pos_label;
            if (v_pos == "center" && h_pos == "center")
                pos_label = "center";
            else
                pos_label = v_pos + "-" + h_pos;

            py::dict zone;
            zone["zone_id"] = std::to_string(r) + "_" + std::to_string(c);
            zone["row"] = r;
            zone["col"] = c;
            zone["position_label"] = pos_label;
            zone["semiotic_label"] = std::string("");
            zone["mean_saliency"] = mean_sal;
            zone["visual_weight"] = visual_weight;
            zone["color_temperature"] = color_temp;
            zone["edge_density"] = edge_density;
            zone["object_count"] = 0;
            zone["tonal_contrast"] = tonal_contrast;
            zone["colour_contrast"] = colour_contrast;
            zone["has_human_figure"] = false;
            zone["foreground_ratio"] = 0.0;
            zone["sharpness"] = sharpness;
            zone["information_value_score"] = info_score;

            zones.append(zone);
        }
    }

    return zones;
}
