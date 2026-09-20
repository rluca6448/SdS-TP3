#include "simulation/Simulation.h"
#include "io/ConfigReader.h"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <filesystem>
#include <limits>
#include <random>
#include <stdexcept>

namespace simulation {

namespace {
constexpr double EPSILON = 1e-12;

int gridCellCount(double boardSize, double particleRadius) {
    if (particleRadius <= 0.0) {
        throw std::invalid_argument("El radio de las particulas debe ser positivo");
    }

    return std::max(
        1,
        static_cast<int>(std::floor(boardSize / (2.0 * particleRadius))));
}

double particleCollisionTime(
    const types::Particle& first,
    const types::Particle& second) {
    const double dx = second.getXLocation() - first.getXLocation();
    const double dy = second.getYLocation() - first.getYLocation();
    const double dvx = second.getXVelocity() - first.getXVelocity();
    const double dvy = second.getYVelocity() - first.getYVelocity();
    const double radiusSum =
        first.getParticleRadius() + second.getParticleRadius();

    const double a = dvx * dvx + dvy * dvy;
    if (a == 0.0) return std::numeric_limits<double>::infinity();

    const double b = 2.0 * (dx * dvx + dy * dvy);
    const double c = dx * dx + dy * dy - radiusSum * radiusSum;
    const double discriminant = b * b - 4.0 * a * c;

    if (discriminant < 0.0 || b >= 0.0) {
        return std::numeric_limits<double>::infinity();
    }

    const double time = (-b - std::sqrt(discriminant)) / (2.0 * a);
    return time > EPSILON ? time : std::numeric_limits<double>::infinity();
}

void resolveParticleCollision(
    types::Particle& first,
    types::Particle& second) {
    const double dx = second.getXLocation() - first.getXLocation();
    const double dy = second.getYLocation() - first.getYLocation();
    const double distance = std::sqrt(dx * dx + dy * dy);

    if (distance == 0.0) {
        throw std::runtime_error("Colision entre particulas con distancia nula");
    }

    const double nx = dx / distance;
    const double ny = dy / distance;
    const double dvx = first.getXVelocity() - second.getXVelocity();
    const double dvy = first.getYVelocity() - second.getYVelocity();
    const double relativeNormalVelocity = dvx * nx + dvy * ny;

    if (relativeNormalVelocity <= 0.0) return;

    const double firstMass = first.getMass();
    const double secondMass = second.getMass();
    const double impulse =
        2.0 * relativeNormalVelocity / (firstMass + secondMass);

    first.setXVelocity(first.getXVelocity() - impulse * secondMass * nx);
    first.setYVelocity(first.getYVelocity() - impulse * secondMass * ny);
    second.setXVelocity(second.getXVelocity() + impulse * firstMass * nx);
    second.setYVelocity(second.getYVelocity() + impulse * firstMass * ny);
}
}

Simulation::Simulation(
    int particleCount,
    double boardLength,
    double boardWidth,
    double goalpostLength,
    double particleRadius,
    double particleMass)
    : particleCount(particleCount),
      currentTime(0),
      goalsCount(0),
      particleRadius(particleRadius),
      particleMass(particleMass),
      t90(std::nullopt),
      board(boardLength, boardWidth, goalpostLength),
      grid(
          boardLength,
          boardWidth,
          gridCellCount(boardLength, particleRadius),
          gridCellCount(boardWidth, particleRadius)),
      queue(particleCount) {}

void Simulation::initialize(
    const std::string& obstacleConfigPath,
    int obstacleCount) {
    if (this->initialized) {
        throw std::logic_error("Simulation can only be initialized once");
    }

    this->initialized = true;

    const std::filesystem::path configPath(obstacleConfigPath);
    if (configPath.has_parent_path()) {
        std::filesystem::create_directories(configPath.parent_path());
    }

    std::ifstream existingConfig(configPath);
    if (existingConfig.good()) {
        existingConfig.close();
        this->obstacles = io::ConfigReader::readObstacles(configPath.string());
    } else {
        this->obstacles = generateObstacles(obstacleCount);

        std::ofstream generatedConfig(configPath);
        if (!generatedConfig) {
            throw std::runtime_error(
                "No se pudo crear el archivo de configuracion: " +
                configPath.string());
        }

        for (const auto& obstacle : obstacles) {
            generatedConfig << obstacle.getX() << " "
                            << obstacle.getY() << " "
                            << obstacle.getRadius() << "\n";
        }
    }

    for (size_t i = 0; i < obstacles.size(); ++i) {
        const auto& obstacle = obstacles[i];
        const double radius = obstacle.getRadius();

        if (radius < particleRadius) {
            throw std::runtime_error(
                "El radio de un obstaculo no puede ser menor al de una particula");
        }

        if (obstacle.getX() - radius < 0.0 ||
            obstacle.getX() + radius > board.getLength() ||
            obstacle.getY() - radius < 0.0 ||
            obstacle.getY() + radius > board.getWidth()) {
            throw std::runtime_error(
                "Hay un obstaculo fuera de los limites del tablero");
        }

        for (size_t j = 0; j < i; ++j) {
            const double dx = obstacle.getX() - obstacles[j].getX();
            const double dy = obstacle.getY() - obstacles[j].getY();
            const double minimumDistance = radius + obstacles[j].getRadius();
            if (dx * dx + dy * dy <
                minimumDistance * minimumDistance - EPSILON) {
                throw std::runtime_error(
                    "La configuracion contiene obstaculos solapados");
            }
        }
    }

    this->particles = generateParticles(particleCount, particleRadius, particleMass);
    grid.rebuild(particles);
    computeInitialCollisionTimes();
}

std::vector<types::Obstacle> Simulation::generateObstacles(int count) const {
    constexpr double obstacleRadius = OBSTACLE_RADIUS;
    constexpr int maxAttempts = 10000;

    std::random_device randomDevice;
    std::mt19937 random(randomDevice());
    std::uniform_real_distribution<double> xDistribution(
        obstacleRadius, board.getLength() - obstacleRadius);
    std::uniform_real_distribution<double> yDistribution(
        obstacleRadius, board.getWidth() - obstacleRadius);

    std::vector<types::Obstacle> generated;
    generated.reserve(count);

    for (int i = 0; i < count; ++i) {
        bool placed = false;

        for (int attempt = 0; attempt < maxAttempts; ++attempt) {
            const double x = xDistribution(random);
            const double y = yDistribution(random);

            bool overlaps = false;
            for (const auto& obstacle : generated) {
                const double dx = x - obstacle.getX();
                const double dy = y - obstacle.getY();
                const double minimumDistance = obstacleRadius + obstacle.getRadius();
                if (dx * dx + dy * dy < minimumDistance * minimumDistance) {
                    overlaps = true;
                    break;
                }
            }

            if (!overlaps) {
                generated.emplace_back(x, y, obstacleRadius);
                placed = true;
                break;
            }
        }

        if (!placed) {
            throw std::runtime_error("No se pudieron generar los obstaculos sin solapamiento");
        }
    }

    return generated;
}

std::vector<types::Particle> Simulation::generateParticles(
    int count,
    double radius,
    double mass) const {
    constexpr int maxAttempts = 10000;

    std::random_device randomDevice;
    std::mt19937 random(randomDevice());
    std::uniform_real_distribution<double> xDistribution(
        radius, board.getLength() - radius);
    std::uniform_real_distribution<double> yDistribution(
        radius, board.getWidth() - radius);

    std::vector<types::Particle> generated;
    generated.reserve(count);

    for (int id = 0; id < count; ++id) {
        bool placed = false;

        for (int attempt = 0; attempt < maxAttempts; ++attempt) {
            const double x = xDistribution(random);
            const double y = yDistribution(random);

            bool overlaps = false;
            for (const auto& particle : generated) {
                const double dx = x - particle.getXLocation();
                const double dy = y - particle.getYLocation();
                const double minimumDistance = 2.0 * radius;
                if (dx * dx + dy * dy < minimumDistance * minimumDistance) {
                    overlaps = true;
                    break;
                }
            }

            if (!overlaps) {
                for (const auto& obstacle : obstacles) {
                    const double dx = x - obstacle.getX();
                    const double dy = y - obstacle.getY();
                    const double minimumDistance = radius + obstacle.getRadius();
                    if (dx * dx + dy * dy < minimumDistance * minimumDistance) {
                        overlaps = true;
                        break;
                    }
                }
            }

            if (!overlaps) {
                generated.emplace_back(id, x, y, radius);
                generated.back().setMass(mass);
                placed = true;
                break;
            }
        }

        if (!placed) {
            throw std::runtime_error(
                "No se pudieron generar las particulas sin solapamiento");
        }
    }

    return generated;
}

void Simulation::computeInitialCollisionTimes() {
    for (auto& particle : particles) {
        recomputeCollisionsFor(particle);
    }
}

void Simulation::step() {
    const types::Event event = queue.pop();
    const double deltaTime = event.time - currentTime;

    if (deltaTime < -EPSILON) {
        throw std::runtime_error("Evento anterior al tiempo actual");
    }

    for (auto& particle : particles) {
        particle.advance(std::max(0.0, deltaTime));
    }
    currentTime = event.time;

    types::Particle& particle = particles.at(event.particleId);
    switch (event.type) {
        case types::EventType::WALL:
            if (board.isGoal(particle, event.side)) {
                checkGoal(particle);
            }
            board.resolveWallCollision(particle, event.side);
            queue.incrementCollisionCount(particle.getId());
            recomputeCollisionsFor(particle);
            break;

        case types::EventType::OBSTACLE:
            obstacles.at(event.otherId).resolveCollision(particle);
            queue.incrementCollisionCount(particle.getId());
            recomputeCollisionsFor(particle);
            break;

        case types::EventType::PARTICLE: {
            types::Particle& other = particles.at(event.otherId);
            resolveParticleCollision(particle, other);
            queue.incrementCollisionCount(particle.getId());
            queue.incrementCollisionCount(other.getId());
            recomputeCollisionsFor(particle);
            recomputeCollisionsFor(other);
            break;
        }
    }

    grid.rebuild(particles);
}

void Simulation::run(int maxTime, io::StateWriter& writer) {
    if (!initialized) {
        initialize();
    }

    writer.writeStateImmediately(particles, currentTime);

    while (currentTime < static_cast<double>(maxTime)) {
        const types::Event event = queue.peek();
        if (event.time > static_cast<double>(maxTime)) {
            const double deltaTime = static_cast<double>(maxTime) - currentTime;
            for (auto& particle : particles) {
                particle.advance(deltaTime);
            }
            currentTime = static_cast<double>(maxTime);
            writer.writeStateImmediately(particles, currentTime);
            break;
        }

        step();
        writer.writeState(particles, currentTime);
    }

    if (currentTime == static_cast<double>(maxTime) || t90.has_value()) {
        writer.writeStateImmediately(particles, currentTime);
    }
}

void Simulation::checkGoal(types::Particle& particle) {
    if (!particle.getUsed()) {
        particle.setUsed();
        ++goalsCount;
        if (!t90.has_value() &&
            static_cast<double>(goalsCount) / particleCount >= 0.9) {
            t90 = currentTime;
        }
    }
}

void Simulation::recomputeCollisionsFor(types::Particle& particle) {
    const int particleId = particle.getId();
    const int snapshotA = queue.getCollisionCount(particleId);

    const types::WallCollision wallCollision =
        board.timeToWallCollision(particle);
    if (std::isfinite(wallCollision.time) && wallCollision.time > EPSILON) {
        queue.push({
            currentTime + wallCollision.time,
            types::EventType::WALL,
            particleId,
            -1,
            snapshotA,
            0,
            wallCollision.side
        });
    }

    for (int obstacleId = 0; obstacleId < static_cast<int>(obstacles.size()); ++obstacleId) {
        const double collisionTime = obstacles[obstacleId].timeToCollision(particle);
        if (std::isfinite(collisionTime) && collisionTime > EPSILON) {
            queue.push({
                currentTime + collisionTime,
                types::EventType::OBSTACLE,
                particleId,
                obstacleId,
                snapshotA,
                0,
                types::Side::NONE
            });
        }
    }

    for (types::Particle* other : grid.neighboursOf(particle)) {
        if (other->getId() <= particleId) {
            continue;
        }

        const double collisionTime = particleCollisionTime(particle, *other);
        if (std::isfinite(collisionTime) && collisionTime > EPSILON) {
            queue.push({
                currentTime + collisionTime,
                types::EventType::PARTICLE,
                particleId,
                other->getId(),
                snapshotA,
                queue.getCollisionCount(other->getId()),
                types::Side::NONE
            });
        }
    }
}

double Simulation::getCurrentlyUsedParticlesPercentage() {
    if (particleCount == 0) return 0.0;
    return static_cast<double>(goalsCount) / particleCount;
}

std::optional<double> Simulation::getT90() {
    return t90;
}

}