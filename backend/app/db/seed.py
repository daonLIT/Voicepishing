from .base import Base, engine, SessionLocal
from .models import AttackMethod, AgentProfile

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # 수법 6개
    methods = [
        (1,"M01","저금리 대출 유도"),
        (2,"M02","기관 사칭"),
        (3,"M03","택배 스미싱"),
        (4,"M04","가족 사칭"),
        (5,"M05","계정 잠김 해결"),
        (6,"M06","투자 리딩"),
    ]
    for i,c,name in methods:
        db.merge(AttackMethod(id=i, code=c, name=name))

    # 공격자 1, 경찰 1, 피해자 5(연령대)
    db.merge(AgentProfile(id=1, role="attacker", name="사기범A", provider="gpt"))
    db.merge(AgentProfile(id=2, role="police", name="경찰", provider="system"))
    age_groups = ["20s","30s","40s","50s","60s+"]
    for i,ag in enumerate(age_groups, start=10):
        db.merge(AgentProfile(
            id=i, role="victim", name=f"시민{ag}", provider="gemini",
            age_group=ag, traits={"finance_lit":0.3,"defense":0.4,"avoidance":0.5}
        ))
    db.commit(); db.close()

if __name__ == "__main__":
    seed()
