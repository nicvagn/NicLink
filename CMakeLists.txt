cmake_minimum_required(VERSION 3.1.0...3.4)

project(NicLink)

cmake_policy(SET CMP0007 NEW) # SET'S LIST NO LONGER IGNORES EMPTY SETS

# set compile settings
set(CMAKE_CXX_STANDARD 11)  # earliest 
set(PYBIND11_PYTHON_VERSION 3.9)
set(CMAKE_CXX_FLAGS "-Wall -Wextra -fPIC")

find_package(pybind11 REQUIRED)

pybind11_add_module(${PROJECT_NAME} NicLink.cpp)

target_compile_definitions(${PROJECT_NAME} PRIVATE VERSION_INFO=${EXAMPLE_VERSION_INFO})
target_include_directories(${PROJECT_NAME} PRIVATE ${PYBIND11_INCLUDE_DIRS})
