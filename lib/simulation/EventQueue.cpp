#include "simulation/EventQueue.h"

namespace simulation {

EventQueue::EventQueue(int particlesCount) : collisionCount(particlesCount, 0) {}

void EventQueue::push(types::Event event) {
    this->queue.push(event);
}

types::Event EventQueue::pop() {
    while (!this->queue.empty()) {
        types::Event event = this->queue.top();
        this->queue.pop();

        if (this->isValid(event)) {
            return event;
        }
    }

    throw std::runtime_error("No valid events in the queue");
}

bool EventQueue::isValid(types::Event event) {
    if (event.snapshotCollisionCountA != this->collisionCount[event.particleId])
        return false;

    if (event.otherId != -1 &&
        event.snapshotCollisionCountB != this->collisionCount[event.otherId])
        return false;

    return true;
}

void EventQueue::incrementCollisionCount(int particleId) {
    this->collisionCount[particleId]++;
}

}