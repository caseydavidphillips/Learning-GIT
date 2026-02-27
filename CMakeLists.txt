cmake_minimum_required(VERSION 3.16)

project(Reelocator VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(reelocator_core ReelocatorCore.cpp)
target_include_directories(reelocator_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_features(reelocator_core PUBLIC cxx_std_17)

add_executable(reelocator Reelocator.cpp)
target_link_libraries(reelocator PRIVATE reelocator_core)

if (MSVC)
    target_compile_options(reelocator PRIVATE /W4 /permissive-)
    target_compile_options(reelocator_core PRIVATE /W4 /permissive-)
else()
    target_compile_options(reelocator PRIVATE -Wall -Wextra -Wpedantic)
    target_compile_options(reelocator_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

enable_testing()

add_executable(reelocator_unit_tests tests/ReelocatorCoreTests.cpp)
target_link_libraries(reelocator_unit_tests PRIVATE reelocator_core)

add_test(NAME reelocator_unit_tests COMMAND reelocator_unit_tests)
