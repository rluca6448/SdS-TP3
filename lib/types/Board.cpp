#include "types/Board.h"

#include <cmath>
#include <limits>

namespace types {

/**
 * Aclaracion: TOP es y=0
 */
Board::Board(double length, double width, double goalpostLength)
    : length(length), width(width), goalpostLength(goalpostLength) {}

WallCollision Board::timeToWallCollision(const types::Particle& particle) const {
    const double r = particle.getParticleRadius();
    const double x = particle.getXLocation();
    const double y = particle.getYLocation();
    const double vx = particle.getXVelocity();
    const double vy = particle.getYVelocity();

    const double inf = std::numeric_limits<double>::infinity();
    double timeLeft = inf;
    double timeRight = inf;
    double timeTop = inf;
    double timeBottom = inf;

    if (vx < 0.0) {
        timeLeft = (x - r) / -vx;
    } else if (vx > 0.0) {
        timeRight = (length - x - r) / vx;
    }

    if (vy < 0.0) {
        timeTop = (y - r) / -vy;
    } else if (vy > 0.0) {
        timeBottom = (width - y - r) / vy;
    }

    WallCollision candidate{inf, Side::NONE};
    if (timeLeft != inf) candidate = {timeLeft, Side::LEFT};
    if (timeRight != inf && timeRight < candidate.time) candidate = {timeRight, Side::RIGHT};
    if (timeTop != inf && timeTop < candidate.time) candidate = {timeTop, Side::TOP};
    if (timeBottom != inf && timeBottom < candidate.time) candidate = {timeBottom, Side::BOTTOM};

    return candidate;
}

void Board::resolveWallCollision(Particle& particle, Side side) const {
    switch (side) {
        case Side::LEFT:
        case Side::RIGHT:
            particle.setXVelocity(-particle.getXVelocity());
            break;
        case Side::TOP:
        case Side::BOTTOM:
            particle.setYVelocity(-particle.getYVelocity());
            break;
        case Side::NONE:
            break;
    }
}

bool Board::isGoal(const Particle& particle, Side side) const {
    if (side != Side::LEFT && side != Side::RIGHT) {
        return false;
    }

    const double halfGoal = goalpostLength / 2.0;
    const double centerY = width / 2.0;
    return std::abs(particle.getYLocation() - centerY) <= halfGoal;
}

double Board::getLength() const {
    return length;
}

double Board::getWidth() const {
    return width;
}

}