#pragma once

#include "types/Particle.h"
#include "types/Side.h"

namespace types {

struct WallCollision {
    double time;
    Side side;
};

class Board {
public:
    WallCollision timeToWallCollision(types::Particle particle);

    void resolveWallCollision(Particle& particle, Side side);

    bool isGoal(Particle particle, Side side);
    
private:
    int length;
    int width;
    int goalpostLength;
    
};
}