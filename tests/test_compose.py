"""The deployment must also accept LXC hosts with equal card/render group IDs."""

import pathlib
import yaml


def test_device_groups_do_not_duplicate_on_lxc():
    compose = pathlib.Path("compose.yaml").read_text()
    compose = compose.replace("${RENDER_GID:?Set RENDER_GID}", "65534")
    compose = compose.replace("${VIDEO_GID:?Set VIDEO_GID}", "65534")
    for service in yaml.safe_load(compose)["services"].values():
        groups = service.get("group_add", [])
        assert len(groups) == len(set(groups))


def test_runtime_caches_do_not_copy_image_build_caches():
    compose = yaml.safe_load(pathlib.Path("compose.yaml").read_text())
    for service in compose["services"].values():
        caches = [v for v in service["volumes"] if isinstance(v, dict)]
        assert len(caches) == 1
        assert caches[0]["target"] == "/root/.cache"
        assert caches[0]["volume"]["nocopy"] is True
    assert "UV_NO_CACHE=1" in pathlib.Path("Dockerfile").read_text()
