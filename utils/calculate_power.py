import pandas as pd

def calculate_power(df, rider_weight, bike_weight, rolling_resistance_coefficient):
    # Use speed and altitude to estimate power
    # Properties we care about:
    # - Gravitational energy
    # - Kinetic energy
    # - Rolling resistance
    # - Air resistance
    # Properties not in scope:
    # - Wind resistance: We don't have wind speed/direction data
    # Mechanical losses: Assume drivetrain efficiency is high enough to not care about it

    # Constants
    g = 9.81  # m/s^2, gravitational acceleration
    system_weight = rider_weight + bike_weight  # kg

    time_steps = df['timestamp'].diff().dt.total_seconds()

    # GPE = m * g * h
    gravitational_potential_energy = system_weight * g * df['altitude']
    delta_gravitational_potential_energy = gravitational_potential_energy.diff().fillna(0)

    gravitational_power = delta_gravitational_potential_energy / time_steps
    # Pad with 0 to account for diff
    df['gravitational_power'] = pd.concat(
        [pd.Series([0]), gravitational_power], ignore_index=True
    )


    # Kinetic energy = 0.5 * m * v^2
    kinetic_energy = 0.5 * system_weight * (df['speed'] ** 2)
    delta_kinetic_energy = kinetic_energy.diff().fillna(0)
    kinetic_power = delta_kinetic_energy / time_steps
    # Pad with 0 to account for diff
    df['kinetic_power'] = pd.concat(
        [pd.Series([0]), kinetic_power], ignore_index=True
    )

    # Frictional resistances
    # Air resistance force = 0.5 * rho * A * C_d * v^2
    # where rho is air density, A is frontal area, C_d is drag coefficient, v is speed,
    # Rolling resistance force = C_r * m * g
    # where C_r is rolling resistance coefficient, m is mass, g is gravitational acceleration,

    # Energy = Force * Distance
    # So, Energy = Force * Speed * Time
    # Power = Energy / Time
    # Thus, Power = Force * Speed

    air_density = 1.225  # kg/m^3, sea level standard air density
    # TODO: Should probably adjust for altitude
    # Using air pressure at 1-mile high at 30C
    # TODO make this a parameter.
    air_density = 0.96  # kg/m^3

    frontal_area = 0.4  # m^2, average frontal area of a cyclist
    # TODO: This is a guess. Maybe this should be a parameter
    drag_coefficient = 0.76  # professional cyclist drag coefficient
    # TODO: This is a guess and testing empirically needs a wind tunnel.

    air_resistance_force = (
        0.5 * air_density * frontal_area * drag_coefficient * (df['speed'] ** 2)
    )
    rolling_resistance_force = (
        rolling_resistance_coefficient * system_weight * g
    )
    total_resistance_force = air_resistance_force + rolling_resistance_force

    frictional_power = (
        total_resistance_force * df['speed']
    )
    df['frictional_power'] = frictional_power
    # Adjust for data sampling rate
    df['frictional_power'] *= df['timestamp'].diff().dt.total_seconds()


    df['calculated_power'] = (
        df['gravitational_power'] +
        df['kinetic_power'] +
        df['frictional_power']
    )

    # Output power cannot be negative. This is a result of braking (or error).
    df['calculated_power'] = df['calculated_power'].clip(lower=0)

    # Smooth out calculated power using a rolling window
    df['calculated_power'] = df['calculated_power'].rolling(window=5, min_periods=1).mean()
