# Heatzy
This a *custom component* for [Home Assistant](https://www.home-assistant.io/). 

With Heatzy, control all your heating systems from anywhere, via your smartphone

There is currently support for the following device types within Home Assistant:
* [Climate sensor](#sensor) with preset mode



![GitHub release](https://img.shields.io/github/release/Cyr-ius/hass-heatzy)


## Configuration

The preferred way to setup the platform is by enabling the discovery component.
Add your equipment via the Integration menu

Otherwise, you can set it up manually in your `configuration.yaml` file:

```yaml
heatzy:
  username: heatzy@ilove.com
  password: heatzy
```
