#include "io/ConfigReader.h"

namespace io {

std::vector<types::Obstacle> ConfigReader::readObstacles(std::string path) {
    std::ifstream file(path);

    if (!file) {
        throw std::runtime_error("No se pudo abrir el archivo de configuracion: " + path);
    }

    std::vector<types::Obstacle> obstacles;
    std::string line;

    while (std::getline(file, line)) {
        if (line.empty()) continue;

        std::istringstream iss(line);
        double x, y, r;

        if (!(iss >> x >> y >> r)) {
            throw std::runtime_error("Linea invalida en config: " + line);
        }

        obstacles.emplace_back(x, y, r);
    }

    return obstacles;
}

}