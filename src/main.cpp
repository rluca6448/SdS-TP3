#include "simulation/Simulation.h"
#include "io/StateWriter.h"

#include <cstdlib>
#include <filesystem>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <string>

int main(int argc, char* argv[]) {
    try {
        const int maxTime = argc > 1 ? std::stoi(argv[1]) : 100;
        const int particleCount = argc > 2 ? std::stoi(argv[2]) : 100;
        const std::string obstacleConfigPath =
            argc > 3 ? argv[3] : "generated/obstacles.txt";
        const std::string outputPath =
            argc > 4 ? argv[4] : "generated/states.txt";
        const int obstacleCount = argc > 5 ? std::stoi(argv[5]) : 3;

        if (maxTime < 0 || particleCount <= 0 || obstacleCount <= 0) {
            throw std::invalid_argument(
                "tmax debe ser no negativo, N y la cantidad de obstaculos "
                "deben ser positivos");
        }

        std::filesystem::create_directories("generated");
        const std::filesystem::path outputFile(outputPath);
        if (outputFile.has_parent_path()) {
            std::filesystem::create_directories(outputFile.parent_path());
        }

        simulation::Simulation simulation(particleCount);
        io::StateWriter writer;
        writer.open(outputPath);

        simulation.initialize(obstacleConfigPath, obstacleCount);
        simulation.run(maxTime, writer);

        writer.close();

        std::cout << "Fu(" << maxTime << ") = "
                  << simulation.getCurrentlyUsedParticlesPercentage()
                  << '\n';

        const auto t90 = simulation.getT90();
        if (t90.has_value()) {
            std::cout << "t90 = " << *t90 << '\n';
        } else {
            std::cout << "t90 no alcanzado\n";
        }

        return EXIT_SUCCESS;
    } catch (const std::exception& exception) {
        std::cerr << "Error: " << exception.what() << '\n';
        return EXIT_FAILURE;
    }
}
