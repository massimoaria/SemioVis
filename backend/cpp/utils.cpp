#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <opencv2/opencv.hpp>

namespace py = pybind11;

/// Convert a pybind11 numpy array (H x W x 3, uint8) to an OpenCV cv::Mat.
/// This is a zero-copy operation when the array is contiguous.
cv::Mat numpy_to_mat_rgb(py::array_t<uint8_t> img) {
    auto buf = img.request();
    if (buf.ndim != 3 || buf.shape[2] != 3) {
        throw std::runtime_error("Expected H x W x 3 uint8 array");
    }
    int h = static_cast<int>(buf.shape[0]);
    int w = static_cast<int>(buf.shape[1]);
    // Wrap numpy data as cv::Mat (no copy). Caller must keep numpy array alive.
    return cv::Mat(h, w, CV_8UC3, buf.ptr);
}

/// Convert a pybind11 numpy array (H x W, uint8) to a single-channel cv::Mat.
cv::Mat numpy_to_mat_gray(py::array_t<uint8_t> img) {
    auto buf = img.request();
    if (buf.ndim != 2) {
        throw std::runtime_error("Expected H x W uint8 array");
    }
    int h = static_cast<int>(buf.shape[0]);
    int w = static_cast<int>(buf.shape[1]);
    return cv::Mat(h, w, CV_8UC1, buf.ptr);
}

/// Convert a pybind11 numpy array (H x W, float32) to a cv::Mat.
cv::Mat numpy_to_mat_float(py::array_t<float> img) {
    auto buf = img.request();
    if (buf.ndim != 2) {
        throw std::runtime_error("Expected H x W float32 array");
    }
    int h = static_cast<int>(buf.shape[0]);
    int w = static_cast<int>(buf.shape[1]);
    return cv::Mat(h, w, CV_32FC1, buf.ptr);
}

/// Convert a cv::Mat (H x W, float32) to a pybind11 numpy array.
/// This copies the data into a new numpy array.
py::array_t<float> mat_to_numpy_float(const cv::Mat& mat) {
    if (mat.type() != CV_32FC1) {
        throw std::runtime_error("Expected CV_32FC1 Mat");
    }
    auto result = py::array_t<float>({mat.rows, mat.cols});
    auto buf = result.mutable_unchecked<2>();
    for (int r = 0; r < mat.rows; ++r)
        for (int c = 0; c < mat.cols; ++c)
            buf(r, c) = mat.at<float>(r, c);
    return result;
}

/// Convert a cv::Mat (H x W x 3, uint8) to a pybind11 numpy array.
/// This copies the data into a new numpy array.
py::array_t<uint8_t> mat_to_numpy_rgb(const cv::Mat& mat) {
    if (mat.type() != CV_8UC3) {
        throw std::runtime_error("Expected CV_8UC3 Mat");
    }
    auto result = py::array_t<uint8_t>({mat.rows, mat.cols, 3});
    auto buf = result.mutable_unchecked<3>();
    for (int r = 0; r < mat.rows; ++r)
        for (int c = 0; c < mat.cols; ++c)
            for (int ch = 0; ch < 3; ++ch)
                buf(r, c, ch) = mat.at<cv::Vec3b>(r, c)[ch];
    return result;
}
