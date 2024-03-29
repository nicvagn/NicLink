cmake_minimum_required(VERSION 3.4...3.18)

project(_niclink LANGUAGES CXX)

# SET'S LIST NO LONGER IGNORES EMPTY SETS
cmake_policy(SET CMP0007 NEW) 
# change relative source path's to absolute
CMAKE_POLICY(SET CMP0076 NEW)
# STILL LOAD PYTHON
CMAKE_POLICY(SET CMP0148 OLD)


# set settings
set(PYBIND11_PYTHON_VERSION 3.12)
# set the wich standard version (C++) the target's will be compiled with. Make it required
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
# using te add_subdir method
find_package(pybind11 CONFIG REQUIRED)

# easylink SDK setup #

# use internal hidapi and spdlog
add_subdirectory("thirdparty/libusb-cmake")
add_subdirectory("thirdparty/hidapi")
add_subdirectory("thirdparty/spdlog")

if(CMAKE_HOST_APPLE)
  link_libraries(hidapi)
elseif(CMAKE_HOST_UNIX)
  link_libraries(hidapi_hidraw)
elseif(CMAKE_HOST_WIN32)
  link_libraries(hidapi)
else()
  link_libraries(hidapi)
endif()


# Debug mode
# ADD_DEFINITIONS(-D_DEBUG_FLAG)

link_libraries(spdlog_header_only)

# pybind and python include dirs
include_directories(PUBLIC ${PYBIND11_INCLUDE_DIRS})
include_directories(PUBLIC ${Python_INCLUDE_DIRS})
include_directories(PUBLIC nicsoft/lib/nicsoft/lib/python3.12/site-packages)

# setup and build the easylink library
set(SOURCE_FILES EasyLink.h EasyLink.cpp easy_link_c.cpp easy_link_c.h)
add_library(easylink SHARED ${SOURCE_FILES})
#add_executable(NicLink)

# link it with the libraies I replaced linking with the created lib to linking directly
link_libraries(easylink hidapi::hidapi spdlog::spdlog pybind11::headers ${PYTHON_LIBRARIES})
# C++ standard 11
# add the pibind module

add_executable(NicLinkcpp NicLink.cpp)
# following pep 8 convention
pybind11_add_module(_niclink NicLink.cpp)
