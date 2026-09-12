#pragma once 

#include "types/Obstacle.h"

#include <vector>
#include <string>

namespace io {

class ConfigReader {
public:
    static std::vector<types::Obstacle> readObstacles(std::string path);
    
};
}