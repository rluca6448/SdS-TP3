#pragma once

#include "types/Particle.h"

namespace types {

class Obstacle {
public:
    Obstacle(double x, double y, double radius);

    double timeToCollision(types::Particle particle);

    void resolveCollision(types::Particle& particle);

    double getX() const;
    double getY() const;
    double getRadius() const;

private:
    double x;
    double y;
    
    double radius;
    
};
}