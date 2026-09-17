cmake_minimum_required(VERSION 3.20)

project(SdS_TP3 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(sds_tp3
    src/main.cpp
    lib/io/ConfigReader.cpp
    lib/io/StateWriter.cpp
    lib/neighbours/Grid.cpp
    lib/simulation/EventQueue.cpp
    lib/simulation/Simulation.cpp
    lib/types/Board.cpp
    lib/types/Obstacle.cpp
    lib/types/Particle.cpp
)

target_include_directories(sds_tp3 PRIVATE include)