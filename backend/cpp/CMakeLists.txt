cmake_minimum_required(VERSION 3.22)
project(semiovis_core CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(OpenCV REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(pybind11 REQUIRED)
find_package(OpenMP)

pybind11_add_module(semiovis_core
    bindings.cpp
    saliency.cpp
    vectors.cpp
    spatial_grid.cpp
    color_features.cpp
    texture_features.cpp
    depth_features.cpp
    utils.cpp
)

target_include_directories(semiovis_core PRIVATE
    ${OpenCV_INCLUDE_DIRS}
    ${EIGEN3_INCLUDE_DIR}
)

target_link_libraries(semiovis_core PRIVATE
    ${OpenCV_LIBS}
    Eigen3::Eigen
)

if(OpenMP_CXX_FOUND)
    target_link_libraries(semiovis_core PRIVATE OpenMP::OpenMP_CXX)
endif()

# Install to backend directory so Python can import it
install(TARGETS semiovis_core DESTINATION ${CMAKE_SOURCE_DIR}/..)
