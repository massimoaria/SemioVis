#include "depth_features.hpp"
#include <opencv2/opencv.hpp>
#include <opencv2/dnn.hpp>
#include <cmath>

static cv::Mat to_mat_rgb(py::array_t<uint8_t>& arr) {
    auto buf = arr.request();
    return cv::Mat(static_cast<int>(buf.shape[0]),
                   static_cast<int>(buf.shape[1]), CV_8UC3, buf.ptr);
}

static py::array_t<float> mat_to_numpy(const cv::Mat& mat) {
    auto result = py::array_t<float>({mat.rows, mat.cols});
    std::memcpy(result.mutable_data(), mat.data, mat.rows * mat.cols * sizeof(float));
    return result;
}

py::array_t<float> estimate_depth_map(
    py::array_t<uint8_t> img_rgb,
    const std::string& model_path)
{
    cv::Mat rgb = to_mat_rgb(img_rgb);
    int orig_h = rgb.rows, orig_w = rgb.cols;

    // If model path is provided, try MiDaS ONNX inference
    if (!model_path.empty()) {
        try {
            cv::dnn::Net net = cv::dnn::readNetFromONNX(model_path);
            if (!net.empty()) {
                // MiDaS v2.1 small expects 256x256 input
                int input_size = 256;

                // Convert RGB to BGR for OpenCV DNN
                cv::Mat bgr;
                cv::cvtColor(rgb, bgr, cv::COLOR_RGB2BGR);

                // Preprocess: resize, float, normalise with ImageNet mean/std
                cv::Mat blob = cv::dnn::blobFromImage(
                    bgr, 1.0 / 255.0,
                    cv::Size(input_size, input_size),
                    cv::Scalar(0.485 * 255, 0.456 * 255, 0.406 * 255),
                    true, false);

                // Further normalise by ImageNet std
                // blob shape: 1 x 3 x 256 x 256
                float* data = reinterpret_cast<float*>(blob.data);
                float stds[] = {0.229f, 0.224f, 0.225f};
                for (int c = 0; c < 3; ++c) {
                    int offset = c * input_size * input_size;
                    for (int i = 0; i < input_size * input_size; ++i) {
                        data[offset + i] /= stds[c];
                    }
                }

                net.setInput(blob);
                cv::Mat output = net.forward();

                // Output shape: 1 x 1 x H x W (or 1 x H x W)
                cv::Mat depth;
                if (output.dims == 4) {
                    depth = cv::Mat(output.size[2], output.size[3], CV_32F,
                                    output.ptr<float>());
                } else if (output.dims == 3) {
                    depth = cv::Mat(output.size[1], output.size[2], CV_32F,
                                    output.ptr<float>());
                } else {
                    depth = output.reshape(1, input_size);
                }

                // Resize to original dimensions
                cv::resize(depth, depth, cv::Size(orig_w, orig_h),
                           0, 0, cv::INTER_LINEAR);

                // Normalise to [0, 1]
                double minv, maxv;
                cv::minMaxLoc(depth, &minv, &maxv);
                if (maxv - minv > 1e-10)
                    depth = (depth - minv) / (maxv - minv);
                else
                    depth = cv::Mat::ones(depth.size(), CV_32F) * 0.5;

                return mat_to_numpy(depth);
            }
        } catch (...) {
            // Fall through to gradient-based estimation
        }
    }

    // Fallback: gradient-based pseudo-depth estimation
    // Uses the assumption that texture density decreases with distance
    cv::Mat gray;
    cv::cvtColor(rgb, gray, cv::COLOR_RGB2GRAY);

    // Laplacian as proxy for detail/texture
    cv::Mat laplacian;
    cv::Laplacian(gray, laplacian, CV_32F);
    cv::Mat abs_lap = cv::abs(laplacian);

    // Smooth heavily to get regional depth estimate
    cv::GaussianBlur(abs_lap, abs_lap, cv::Size(51, 51), 15.0);

    // Add vertical gradient prior (bottom = near, top = far for most images)
    cv::Mat vert_prior(orig_h, orig_w, CV_32F);
    for (int r = 0; r < orig_h; ++r) {
        float v = static_cast<float>(r) / orig_h;  // 0=top(far), 1=bottom(near)
        for (int c = 0; c < orig_w; ++c) {
            vert_prior.at<float>(r, c) = v;
        }
    }

    // Normalise texture map
    double minv, maxv;
    cv::minMaxLoc(abs_lap, &minv, &maxv);
    if (maxv - minv > 1e-10)
        abs_lap = (abs_lap - minv) / (maxv - minv);
    else
        abs_lap = cv::Mat::ones(abs_lap.size(), CV_32F) * 0.5;

    // Combine: high texture = near (low depth value)
    cv::Mat depth = 0.6 * vert_prior + 0.4 * abs_lap;

    cv::minMaxLoc(depth, &minv, &maxv);
    if (maxv - minv > 1e-10)
        depth = (depth - minv) / (maxv - minv);

    return mat_to_numpy(depth);
}
