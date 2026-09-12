#pragma once

#include "types/EventType.h"

namespace types {

class Event {
public:
    bool operator<(const Event& other) const;

private:
    double type;
    types::EventType type;
    
    double radius;

    int particleId;
    int otherId;

    int snapshotCollisionCountA;
    int snapshotCollisionCountB;

    int creationTime;
    
};
}