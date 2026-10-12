from agents.state import AgentState
def make_resolver_node(join_graph):

    def resolver_node(state:AgentState):
        linking = state["linking"]
        extraction = state["extraction"]
        