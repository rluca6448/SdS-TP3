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
    Board(double length = 1.20, double width = 0.68, double goalpostLength = 0.20);

    WallCollision timeToWallCollision(const types::Particle& particle) const;

    void resolveWallCollision(Particle& particle, Side side) const;

    bool isGoal(const Particle& particle, Side side) const;

    double getLength() const;
    double getWidth() const;

private:
    double length;
    double width;
    double goalpostLength;
};
}