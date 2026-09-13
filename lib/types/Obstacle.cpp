#include "types/Obstacle.h"

#include <cmath>

namespace types {

double Obstacle::timeToCollision(types::Particle particle) {
    double xDist = particle.getXLocation() - this->x;
    double yDist = particle.getYLocation() - this->y;
    double radiusSum = particle.getParticleRadius() + this->radius;

    double vx = particle.getXVelocity();
    double vy = particle.getYVelocity();

    double a = vx * vx + vy * vy;

    if (a == 0) {
        return INFINITY;
    }

    double b = 2 * (xDist * vx + yDist * vy);
    double c = xDist * xDist + yDist * yDist - radiusSum * radiusSum;

    double disc = b * b - 4 * a * c;

    if (disc < 0) {
        return INFINITY;
    }

    double sqrtDisc = sqrt(disc);
    double r1 = (-b - sqrtDisc) / (2 * a);
    double r2 = (-b + sqrtDisc) / (2 * a);

    if (r1 > 0) return r1;
    if (r2 > 0) return r2;

    return INFINITY;
}

void Obstacle::resolveCollision(types::Particle& particle) {
    double dx = particle.getXLocation() - this->x;
    double dy = particle.getYLocation() - this->y;
    double dist = sqrt(dx * dx + dy * dy);

    double enx = dx / dist;
    double eny = dy / dist;

    double etx = -eny;
    double ety = enx;

    double alpha = atan2(eny, enx);

    double cosA = cos(alpha);
    double sinA = sin(alpha);

    double cn = 1.0;
    double ct = 1.0;

    double vx = particle.getXVelocity();
    double vy = particle.getYVelocity();

    double newVx = (-cn * cosA * cosA + ct * sinA * sinA) * vx
                 + (-(cn + ct) * sinA * cosA) * vy;

    double newVy = (-(cn + ct) * sinA * cosA) * vx
                 + (-cn * sinA * sinA + ct * cosA * cosA) * vy;

    particle.setXVelocity(newVx);
    particle.setYVelocity(newVy);
}

}