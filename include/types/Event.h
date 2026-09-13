#pragma once

#include "types/EventType.h"
#include "types/Side.h"

namespace types {

struct Event {
    double time;
    types::EventType type;

    int particleId;
    int otherId; 
    
    int snapshotCollisionCountA;
    int snapshotCollisionCountB;  

    types::Side side;             
};

struct EventComparator {
    bool operator()(const Event& a, const Event& b) const {
        return a.time > b.time;
    }
};
}