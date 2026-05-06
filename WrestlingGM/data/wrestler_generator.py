"""
DEPRECATED: This module is kept only for backwards compatibility.
Use data/wrestler_pool.py instead.
"""

from data.wrestler_pool import WrestlerPool


def generate_free_agents(count=50, level=1):
    """DEPRECATED: Use WrestlerPool.generate_starter_pool() instead"""
    pool = WrestlerPool()
    return pool.generate_starter_pool(target_size=count, include_licensed=True)


def get_free_agents_for_level(level):
    """DEPRECATED: Use WrestlerPool methods instead"""
    pool = WrestlerPool()
    return pool.generate_starter_pool(target_size=100, include_licensed=True)


def refresh_free_agent_pool(current_agents, level, max_agents=200):
    """DEPRECATED: Use WrestlerPool.generate_weekly_refresh() instead"""
    pool = WrestlerPool()
    new_agents = pool.generate_weekly_refresh(
        current_pool_size=len(current_agents),
        target_pool_size=max_agents,
    )
    current_agents.extend(new_agents)
    return current_agents
