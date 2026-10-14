
## Processed outputs

The processed diagnostics are averaged over the final three years of each forcing plateau.

### Available variables

- `melt_0d`: Ice-shelf-averaged basal melt rate.
- `melt_2d`: Spatial distribution of basal melt rate.
- `dzT`: Temperature stratification averaged over the polynya region.
- `qfw`: Freshwater flux at the ice–ocean interface, averaged over the ice shelf.
- `Sb_qfw`: Equivalent salinity flux at the ice–ocean interface, averaged over the ice shelf.
- `T_bot`: Bottom-cell temperature averaged over the polynya region.
- `w_std`: Temporal standard deviation of vertical velocity, averaged over the polynya region.
- `utbl2_x50km`: Squared horizontal velocity in the Losch boundary layer at x = 50 km.
- `MOC`: Meridional overturning circulation.
- `BSF`: Barotropic streamfunction.

### Supplementary simulations

For a few forcing plateaus, the steady-state diagnostics could not be reconstructed from `../monthly_out` because the simulations had been restarted to reach steady state.

For these cases, supplementary 10-year simulations were performed under the same forcing conditions, and the diagnostics were averaged over their final three years.

The affected experiments and forcing values are:

| Experiment | Transition | Fs (g/m²/s) |
|------------|------------|-----------------|
| `SSS33.8`  | Warm-to-cold and cold-to-warm | 0.030, 0.035 |
| `SBS34.7`  | Warm-to-cold and cold-to-warm | 0.030, 0.035 |
| `NUH32`    | Warm-to-cold | 0.030 |
| `NUH32`    | Cold-to-warm | 0.015 |
| `NUH1.3`   | Cold-to-warm | 0.030 |

All other diagnostics can be obtained directly from the `../monthly_out` simulations.

  
