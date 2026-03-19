#include "color_features.hpp"
#include <opencv2/opencv.hpp>
#include <sstream>
#include <iomanip>
#include <cmath>
#include <algorithm>
#include <vector>

static cv::Mat to_mat_rgb(py::array_t<uint8_t>& arr) {
    auto buf = arr.request();
    return cv::Mat(static_cast<int>(buf.shape[0]),
                   static_cast<int>(buf.shape[1]), CV_8UC3, buf.ptr);
}

py::dict compute_modality_cues(
    py::array_t<uint8_t> img_rgb)
{
    // 8 modality markers (Kress & van Leeuwen, 2006, pp.160-163)
    cv::Mat rgb = to_mat_rgb(img_rgb);
    int h = rgb.rows, w = rgb.cols;

    // Convert to various colour spaces
    cv::Mat hsv, lab, gray;
    cv::cvtColor(rgb, hsv, cv::COLOR_RGB2HSV);
    cv::cvtColor(rgb, lab, cv::COLOR_RGB2Lab);
    cv::cvtColor(rgb, gray, cv::COLOR_RGB2GRAY);

    std::vector<cv::Mat> hsv_ch, lab_ch;
    cv::split(hsv, hsv_ch);
    cv::split(lab, lab_ch);

    // 1. Colour saturation (p.160): mean saturation [0-1]
    double colour_saturation = cv::mean(hsv_ch[1])[0] / 255.0;

    // 2. Colour differentiation (p.160): number of distinct hue clusters
    // Count occupied hue bins (quantise to 12 sectors of 15 degrees)
    cv::Mat hue_mask;
    cv::threshold(hsv_ch[1], hue_mask, 25, 255, cv::THRESH_BINARY);  // ignore very low sat
    int n_bins = 12;
    std::vector<int> hue_hist(n_bins, 0);
    for (int r = 0; r < h; ++r) {
        for (int c = 0; c < w; ++c) {
            if (hue_mask.at<uint8_t>(r, c) > 0) {
                int bin = hsv_ch[0].at<uint8_t>(r, c) * n_bins / 180;
                bin = std::min(bin, n_bins - 1);
                hue_hist[bin]++;
            }
        }
    }
    int occupied = 0;
    int min_pixels = (h * w) / 200;  // at least 0.5% of pixels
    for (int b : hue_hist)
        if (b > min_pixels) occupied++;
    double colour_differentiation = std::min(1.0, static_cast<double>(occupied) / 8.0);

    // 3. Colour modulation (p.160): within-hue variation
    // Standard deviation of saturation within each occupied hue bin
    cv::Scalar sat_mean, sat_std;
    cv::meanStdDev(hsv_ch[1], sat_mean, sat_std, hue_mask);
    double colour_modulation = std::min(1.0, sat_std[0] / 80.0);

    // 4. Contextualization (p.161): background detail/complexity
    // Edge density in periphery (outer 20% border)
    int border = std::max(1, std::min(h, w) / 5);
    cv::Mat periphery_mask = cv::Mat::zeros(h, w, CV_8UC1);
    periphery_mask(cv::Rect(0, 0, w, border)).setTo(255);
    periphery_mask(cv::Rect(0, h - border, w, border)).setTo(255);
    periphery_mask(cv::Rect(0, 0, border, h)).setTo(255);
    periphery_mask(cv::Rect(w - border, 0, border, h)).setTo(255);

    cv::Mat edges;
    cv::Canny(gray, edges, 50, 150);
    cv::Mat periph_edges;
    cv::bitwise_and(edges, periphery_mask, periph_edges);
    double periph_edge_density = cv::countNonZero(periph_edges) /
        static_cast<double>(cv::countNonZero(periphery_mask) + 1);
    double contextualization = std::min(1.0, periph_edge_density * 10.0);

    // 5. Representation (p.161): image detail level (high-frequency energy)
    cv::Mat laplacian;
    cv::Laplacian(gray, laplacian, CV_64F);
    cv::Scalar lap_mean, lap_std;
    cv::meanStdDev(laplacian, lap_mean, lap_std);
    double representation = std::min(1.0, lap_std[0] / 40.0);

    // 6. Depth (p.162): estimated from gradient magnitude distribution
    // Images with strong perspective have more varied gradient magnitudes
    cv::Mat grad_x, grad_y, grad_mag;
    cv::Sobel(gray, grad_x, CV_64F, 1, 0, 3);
    cv::Sobel(gray, grad_y, CV_64F, 0, 1, 3);
    cv::magnitude(grad_x, grad_y, grad_mag);

    // Compare gradient magnitude in top vs bottom halves (perspective cue)
    cv::Mat top_half = grad_mag(cv::Rect(0, 0, w, h / 2));
    cv::Mat bot_half = grad_mag(cv::Rect(0, h / 2, w, h - h / 2));
    double top_grad = cv::mean(top_half)[0];
    double bot_grad = cv::mean(bot_half)[0];
    double grad_ratio = (bot_grad > 1e-10) ? top_grad / bot_grad : 1.0;
    // In images with depth, foreground (bottom) has more detail than background (top)
    double depth = std::min(1.0, std::abs(1.0 - grad_ratio) * 2.0);

    // 7. Illumination (p.162): light/shade interplay
    // Variance of brightness across the image
    cv::Scalar gray_mean, gray_std;
    cv::meanStdDev(gray, gray_mean, gray_std);
    double illumination = std::min(1.0, gray_std[0] / 80.0);

    // 8. Brightness (p.162): number of distinct brightness levels
    // Histogram bin occupancy
    int brightness_bins = 16;
    cv::Mat gray_float;
    gray.convertTo(gray_float, CV_32F);
    float ranges[] = {0, 256};
    const float* hist_ranges = ranges;
    int hist_size = brightness_bins;
    cv::Mat hist;
    cv::calcHist(&gray_float, 1, 0, cv::Mat(), hist, 1, &hist_size, &hist_ranges);
    int occupied_brightness = 0;
    float min_count = static_cast<float>(h * w) / (brightness_bins * 4);
    for (int i = 0; i < brightness_bins; ++i)
        if (hist.at<float>(i) > min_count) occupied_brightness++;
    double brightness = static_cast<double>(occupied_brightness) / brightness_bins;

    py::dict cues;
    cues["colour_saturation"] = colour_saturation;
    cues["colour_differentiation"] = colour_differentiation;
    cues["colour_modulation"] = colour_modulation;
    cues["contextualization"] = contextualization;
    cues["representation"] = representation;
    cues["depth"] = depth;
    cues["illumination"] = illumination;
    cues["brightness"] = brightness;
    return cues;
}

py::list extract_color_palette(
    py::array_t<uint8_t> img_rgb,
    int k,
    int max_iter)
{
    cv::Mat rgb = to_mat_rgb(img_rgb);
    int h = rgb.rows, w = rgb.cols;

    // Downsample for speed
    cv::Mat small;
    if (h * w > 500 * 500) {
        double scale = 500.0 / std::max(h, w);
        cv::resize(rgb, small, cv::Size(), scale, scale, cv::INTER_AREA);
    } else {
        small = rgb;
    }

    // Reshape to Nx3 float matrix
    cv::Mat pixels = small.reshape(1, small.rows * small.cols);
    pixels.convertTo(pixels, CV_32F);

    // k-means clustering
    cv::Mat labels, centres;
    cv::TermCriteria criteria(cv::TermCriteria::EPS + cv::TermCriteria::MAX_ITER,
                              max_iter, 1.0);
    cv::kmeans(pixels, k, labels, criteria, 3, cv::KMEANS_PP_CENTERS, centres);

    // Count pixels per cluster
    std::vector<int> counts(k, 0);
    for (int i = 0; i < labels.rows; ++i)
        counts[labels.at<int>(i)]++;

    int total = labels.rows;

    // Build sorted palette
    struct Swatch {
        int r, g, b;
        double proportion;
    };
    std::vector<Swatch> swatches;

    for (int i = 0; i < k; ++i) {
        int cr = static_cast<int>(centres.at<float>(i, 0));
        int cg = static_cast<int>(centres.at<float>(i, 1));
        int cb = static_cast<int>(centres.at<float>(i, 2));
        cr = std::clamp(cr, 0, 255);
        cg = std::clamp(cg, 0, 255);
        cb = std::clamp(cb, 0, 255);
        swatches.push_back({cr, cg, cb, static_cast<double>(counts[i]) / total});
    }

    std::sort(swatches.begin(), swatches.end(),
              [](const Swatch& a, const Swatch& b) { return a.proportion > b.proportion; });

    py::list palette;
    for (auto& s : swatches) {
        std::ostringstream hex;
        hex << "#" << std::hex << std::setfill('0')
            << std::setw(2) << s.r
            << std::setw(2) << s.g
            << std::setw(2) << s.b;

        py::dict entry;
        entry["rgb"] = py::make_tuple(s.r, s.g, s.b);
        entry["hex"] = hex.str();
        entry["proportion"] = s.proportion;
        palette.append(entry);
    }

    return palette;
}
