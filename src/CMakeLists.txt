cmake_minimum_required(VERSION 3.4...3.18)

# SET'S LIST NO LONGER IGNORES EMPTY SETS
cmake_policy(SET CMP0007 NEW) 
# change relative source path's to absolute
CMAKE_POLICY(SET CMP0076 NEW)
# STILL LOAD PYTHON
CMAKE_POLICY(SET CMP0148 OLD)


project(niclink LANGUAGES CXX)


#TODO: set for your system
# NOTE: removed as not debbuging c++ code link_libraries(spdlog_header_only)
set(SPDLOG OFF) # Very fast, header-only/compiled, C++ logging library.
# NOTE: not needed if using hidraw backend to libusb
set(LIBUSB ON) 
# NOTE: adjust if using HIDRAW
# see https://github.com/libusb/libusb
# see thirdparty/hidapi/README.md
set(HIDRAW OFF)
# NOTE: This is a linux kernal usb backend
# see thirdparty/hidapi/README.md
# WARNING: only tested w 3.12
set(PY_VERSION 3.12)
# the version of python to use, for the pybing module, and etc
########################## CONFIG DONE ############################

# set settings
set(PYBIND11_PYTHON_VERSION ${PY_VERSION})
# set the wich standard version (C++) the target's will be compiled with.
# Make it required
set(CMAKE_CXX_STANDARD 11)
set(CXX_STANDARD_REQUIRED On)
set(CMAKE_CXX_FLAGS "-Wall -Wextra -fPIC")
# set the standard version of C
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_FLAGS "-Wall -Wextra -fPIC")
set(CMAKE_C_STANDARD_REQUIRED ON)

# find all the required packages
# pyBind
find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(PythonLibs REQUIRED)

# pybind11 using the add_subdir method
add_subdirectory("thirdparty/pybind11")

# add the pibind module
pybind11_add_module(_niclink NicLink.cpp)

if(HIDRAW)
    set(HIDAPI_WITH_HIDRAW ON) # for my settup
    # do not build libusb
    option(HIDAPI_WITH_LIBUSB "Build LIBUSB-based implementation of HIDAPI" OFF)
endif()
# NOTE: THIS IS NOT NEEDED IF BUILDING WITH THE HIDRAW BACKEND
if(LIBUSB)
    add_subdirectory("thirdparty/libusb-cmake")
    option(HIDAPI_WITH_LIBUSB "Build LIBUSB-based implementation of HIDAPI" ON)
endif()
if(SPDLOG) #C++ logging
    add_subdirectory("thirdparty/spdlog")
endif()

# human interface api
add_subdirectory("thirdparty/hidapi-git")

if(CMAKE_HOST_APPLE)
    target_link_libraries(_niclink PRIVATE hidapi)
elseif(CMAKE_HOST_UNIX)
  target_link_libraries(_niclink PRIVATE hidapi_hidraw)
elseif(CMAKE_HOST_WIN32)
    target_link_libraries(_niclink PRIVATE hidapi)
else()
    target_link_libraries(_niclink PRIVATE hidapi)
endif()

# pybind and python include dirs
include_directories(PUBLIC ${PYBIND11_INCLUDE_DIRS})
include_directories(PUBLIC ${Python_INCLUDE_DIRS})
include_directories(PUBLIC nicsoft/lib/nicsoft/lib/python3.12/site-packages)

# setup and link the easylink library
set(SOURCE_FILES EasyLink.h EasyLink.cpp easy_link_c.cpp easy_link_c.h)
target_sources(_niclink PUBLIC ${SOURCE_FILES})

# link pybind11 module to EasyLink
target_link_libraries(
    _niclink 
    PRIVATE
    pybind11::headers
    ${PYTHON_LIBRARIES}
)

