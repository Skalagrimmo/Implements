from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.world_state import initialize_world_state, apply_world_event, replay_world_events
from pixelgen.world_state_integrity import validate_world_state
from pixelgen.progression import simulate_progression

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")
dims=[(1,1),(2,2),(4,3),(6,5)]
cases=0
mutated=0

for seed in range(-15,25):
    for cols,rows in dims:
        world=generate_gameplay_world(profile,seed,cols,rows,4)
        state=initialize_world_state(world)
        assert validate_world_state(world,state)==[]

        events=[]
        fronts=sorted(state["fronts"])
        territories=sorted(state["territories"])

        if fronts:
            events.append({
                "event_type":"front_escalation",
                "target_id":fronts[0],
                "amount":0.17,
                "source":"fuzz",
            })
        if territories:
            events.append({
                "event_type":"territory_alert",
                "target_id":territories[-1],
                "amount":0.11,
                "source":"fuzz",
            })

        for event in events:
            state=apply_world_event(world,state,event)

        assert validate_world_state(world,state)==[]
        assert replay_world_events(world,state["event_log"])==state

        sim=simulate_progression(world)
        assert sim["final_sector_reachable"] and sim["all_sectors_reachable"]

        if events:
            mutated+=1
        cases+=1

print(f"PixelGen v0.8.0 dynamic-state fuzz passed: {cases} worlds, {mutated} mutated")
