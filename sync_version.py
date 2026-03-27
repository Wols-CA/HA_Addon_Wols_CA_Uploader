import yaml

# Copy version from config/version.yaml to config.yaml
with open('config/version.yaml') as f:
    version_data = yaml.safe_load(f)

with open('wols_ca_uploader/config.yaml') as f:
    config_data = yaml.safe_load(f)

version_data['version'] = config_data.get('version')

with open('config/version.yaml', 'w') as f:
    yaml.safe_dump(version_data, f)