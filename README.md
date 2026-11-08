# OdoPlan for Home Assistant

[OdoPlan](https://www.odoplan.ch) breaks your kilometre allowance for a lease or an insurance policy down to every single day. This integration brings your cars' numbers into Home Assistant as sensors and, if you like, enters the odometer for you.

## What you get

One device per car, with these sensors:

| Sensor | Meaning |
|---|---|
| Buffer | Kilometres ahead of (positive) or behind (negative) plan |
| Status | On plan, slightly over or over |
| Left this week / Left this month | What you can still drive until Sunday or the end of the month |
| Next month | The budget for next month |
| Odometer, Last reading | The latest reading and its date |
| Driven since contract start, Allowed until today | The two lines of the chart in OdoPlan |
| Pace, Ordinary day | Kilometres per day lately, and without holidays and long trips |
| Left in contract, Forecast at contract end, Contract end | Only with a contract length |
| Forecast for the contract year | Where you will land at the end of the contract year |
| Extra kilometres, Extra kilometre cost | What would be too much in the end and what it would cost (the cost only with a price per extra kilometre) |
| Next contract | The suggested allowance per year |
| Driven electrically | Plug-in hybrids only |
| Fuel consumption, Energy per 100 km | From fuel stops and charging sessions |

Plus the action **OdoPlan: Enter odometer** (`odoplan.add_reading`). Home Assistant fetches the numbers from OdoPlan every 15 minutes. The entities are translated into English, German, French and Italian.

## Installation

1. In HACS, open ⋮ at the top right → *Custom repositories*, add this repository's address with the type *Integration*.
2. Search HACS for **OdoPlan**, download it and restart Home Assistant.
3. Go to *Settings → Devices & services → Add integration → OdoPlan*.
4. Enter your key. You create it in OdoPlan on a car's **Automation** page; it works for all your cars.

Without HACS: copy the folder `custom_components/odoplan` into the `custom_components` folder of your Home Assistant configuration and restart.

## Entering the odometer every evening

If Home Assistant knows your car's odometer, for example from the manufacturer's integration:

```yaml
automation:
  - alias: "OdoPlan: enter odometer"
    triggers:
      - trigger: time
        at: "22:00:00"
    actions:
      - action: odoplan.add_reading
        data:
          device_id: YOUR_DEVICE_ID   # pick the car in the action editor
          km: "{{ states('sensor.your_car_mileage') }}"
```

One reading per day; a new value on the same day corrects it. As in the app, the reading has to fit the others. If you use the `rest_command` from OdoPlan's Automation page so far, this action replaces it.

## Example dashboard

```yaml
type: vertical-stack
cards:
  - type: gauge
    entity: sensor.family_car_buffer
    min: -1000
    max: 1000
    severity:
      green: 0
      yellow: -300
      red: -1000
  - type: entities
    entities:
      - sensor.family_car_status
      - sensor.family_car_left_this_month
      - sensor.family_car_forecast_at_contract_end
      - sensor.family_car_extra_kilometre_cost
  - type: history-graph
    hours_to_show: 720
    entities:
      - sensor.family_car_buffer
```

The sensors' entity IDs depend on your car's name and on Home Assistant's language.

## Privacy

The integration only talks to the address you enter when setting it up (as a rule `https://www.odoplan.ch`) and only sends your key and the readings you enter. How OdoPlan handles your data is described in its [privacy policy](https://www.odoplan.ch/datenschutz).

## License

MIT, see [LICENSE](LICENSE).
