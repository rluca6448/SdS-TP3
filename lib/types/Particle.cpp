#include "types/Particle.h"

namespace types {

namespace {
    thread_local std::mt19937 velocityRng{std::random_device{}()};
}

Particle::Particle(int id, double x, double y, double particleRadius)
    : id(id), particleRadius(particleRadius), used(false), x(x), y(y) {

    double speed = 0.03;
    std::uniform_real_distribution<double> angleDist(0.0, 2 * M_PI);
    double theta = angleDist(velocityRng);
    this->xVelocity = speed * std::cos(theta);
    this->yVelocity = speed * std::sin(theta);
}

Particle::Particle(int id, double x, double y)
    : id(id), used(false), x(x), y(y), particleRadius(0.0) {
    
    double speed = 0.03;
    std::uniform_real_distribution<double> angleDist(0.0, 2 * M_PI);
    double theta = angleDist(velocityRng);
    this->xVelocity = speed * std::cos(theta);
    this->yVelocity = speed * std::sin(theta);
}

int Particle::getId() const { return id; }

double Particle::getXLocation() const { return x; }
void Particle::setXLocation(double x) { this->x = x; }

double Particle::getYLocation() const { return y; }
void Particle::setYLocation(double y) { this->y = y; }

double Particle::getXVelocity() const { return xVelocity; }
void Particle::setXVelocity(double xVelocity) { this->xVelocity = xVelocity; }

double Particle::getYVelocity() const { return yVelocity; }
void Particle::setYVelocity(double yVelocity) { this->yVelocity = yVelocity; }

double Particle::getParticleRadius() const { return particleRadius; }

bool Particle::getUsed() const { return used; }
void Particle::setUsed() { this->used = true; }

void Particle::setMass(double mass) { this->mass = mass; }
double Particle::getMass() const { return mass; }

void Particle::setCellXIndex(int cellXIndex) { this->cellXIndex = cellXIndex; }
int Particle::getCellXIndex() const { return cellXIndex; }

void Particle::setCellYIndex(int cellYIndex) { this->cellYIndex = cellYIndex; }
int Particle::getCellYIndex() const { return cellYIndex; }

void Particle::advance(double dt) {
    this->setXLocation(this->getXLocation() + this->getXVelocity() * dt);
    this->setYLocation(this->getYLocation() + this->getYVelocity() * dt);
}

std::string Particle::toString() const {
    std::ostringstream oss;
    oss << x << " " << y << " " << xVelocity << " " << yVelocity;
    return oss.str();
}

bool Particle::operator==(const Particle& other) const {
    return id == other.id;
}

} 
