#pragma once

#include "types/Particle.h"

namespace types {

class Obstacle {
public:
    double timeToCollision(types::Particle particle);

    void resolveCollision(types::Particle& particle);

private:
    double x;
    double y;
    
    double radius;
    
};
}