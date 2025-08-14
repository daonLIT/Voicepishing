import json
class VictimMemory:
    def __init__(self, victim_id:int, edu_rules:list[dict]|None=None):
        self.victim_id = victim_id
        self.edu_rules = edu_rules or []
    def rules_json(self): return json.dumps(self.edu_rules, ensure_ascii=False)
