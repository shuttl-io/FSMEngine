
class EngineException(Exception): pass
class EmptyStartException(EngineException): pass

class EdgeConditionException(EngineException):
    def __init__(self, msg):
        super(EdgeConditionException, self).__init__(msg)
