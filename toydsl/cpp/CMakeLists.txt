cmake_minimum_required(VERSION 3.12)
project(dslgen)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR
   CMAKE_CXX_COMPILER_ID MATCHES "GNU" OR
   CMAKE_CXX_COMPILER_ID MATCHES "Intel")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wpedantic -Wno-deprecated")
    set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g -ggdb -fno-omit-frame-pointer")
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -march=native -DNDEBUG -s -flto")
endif()

find_package(Python3 REQUIRED COMPONENTS Development)
find_package(Boost 1.68 REQUIRED COMPONENTS python numpy)

add_library(tsc INTERFACE)
target_include_directories(tsc INTERFACE "${CMAKE_CURRENT_LIST_DIR}/include")

set(SOURCE_DIR "${CMAKE_CURRENT_LIST_DIR}" CACHE FILEPATH "directory where 'dslgen.cpp' is located")

set(CMAKE_SHARED_MODULE_PREFIX "")
add_library(dslgen MODULE "${SOURCE_DIR}/dslgen.cpp")

target_link_libraries(dslgen
    Python3::Module
    Python3::Python
    Boost::python
    Boost::numpy
    tsc
)
