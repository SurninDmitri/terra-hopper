class TerraHopperError(Exception):
    pass


class NoTransportError(TerraHopperError):
    pass


class UnknownActionError(TerraHopperError):
    pass


class InvalidLocationError(TerraHopperError):
    pass


class NotEnoughStrengthError(TerraHopperError):
    pass


class NotEnoughEnergyError(TerraHopperError):
    pass
