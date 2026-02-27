cmake_minimum_required(VERSION 3.16)

project(Reelocator VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(reelocator Reelocator.cpp)

target_compile_features(reelocator PRIVATE cxx_std_17)

if (MSVC)
    target_compile_options(reelocator PRIVATE /W4 /permissive-)
else()
    target_compile_options(reelocator PRIVATE -Wall -Wextra -Wpedantic)
endif()
