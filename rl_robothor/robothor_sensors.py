import typing
from typing import Any, Dict, Optional

import gym
import numpy as np
import quaternion  # noqa # pylint: disable=unused-import
from torchvision import transforms

from utils.tensor_utils import ScaleBothSides
from rl_base.sensor import Sensor, RGBSensor, DepthSensor
from rl_base.task import Task
from rl_robothor.robothor_environment import RoboThorEnvironment
from rl_robothor.robothor_tasks import PointNavTask


class RGBSensorRoboThor(RGBSensor[RoboThorEnvironment, Task[RoboThorEnvironment]]):
    """Sensor for RGB images in RoboTHOR.

    Returns from a running RoboThorEnvironment instance, the current RGB
    frame corresponding to the agent's egocentric view.
    """

    def frame_from_env(self, env: RoboThorEnvironment) -> np.ndarray:
        return env.current_frame.copy()


class GPSCompassSensorRoboThor(Sensor[RoboThorEnvironment, PointNavTask]):
    def __init__(self, config: Dict[str, Any], *args: Any, **kwargs: Any):
        super().__init__(config, *args, **kwargs)

        self.observation_space = gym.spaces.Box(
            low=np.finfo(np.float32).min,
            high=np.finfo(np.float32).max,
            shape=(2,),
            dtype=np.float32,
        )

    def _get_uuid(self, *args: Any, **kwargs: Any) -> str:
        return "target_coordinates_ind"

    def _get_observation_space(self) -> gym.spaces.Box:
        return typing.cast(gym.spaces.Box, self.observation_space)

    def _compute_pointgoal(self, source_position, source_rotation, goal_position):
        direction_vector = goal_position - source_position
        direction_vector_agent = self.quaternion_rotate_vector(
            source_rotation.inverse(), direction_vector
        )

        rho, phi = GPSCompassSensorRoboThor.cartesian_to_polar(
            direction_vector_agent[2], -direction_vector_agent[0]
        )
        return np.array([rho, phi], dtype=np.float32)

    @staticmethod
    def quaternion_from_y_angle(angle: float) -> np.quaternion:
        r"""Creates a quaternion from rotation angle around y axis
        """
        return GPSCompassSensorRoboThor.quaternion_from_coeff(
            np.array(
                [0.0, np.sin(np.pi * angle / 360.0), 0.0, np.cos(np.pi * angle / 360.0)]
            )
        )

    @staticmethod
    def quaternion_from_coeff(coeffs: np.ndarray) -> np.quaternion:
        r"""Creates a quaternions from coeffs in [x, y, z, w] format
        """
        quat = np.quaternion(0, 0, 0, 0)
        quat.real = coeffs[3]
        quat.imag = coeffs[0:3]
        return quat

    @staticmethod
    def cartesian_to_polar(x, y):
        rho = np.sqrt(x ** 2 + y ** 2)
        phi = np.arctan2(y, x)
        return rho, phi

    @staticmethod
    def quaternion_rotate_vector(quat: np.quaternion, v: np.array) -> np.array:
        r"""Rotates a vector by a quaternion
        Args:
            quaternion: The quaternion to rotate by
            v: The vector to rotate
        Returns:
            np.array: The rotated vector
        """
        vq = np.quaternion(0, 0, 0, 0)
        vq.imag = v
        return (quat * vq * quat.inverse()).imag

    def get_observation(
        self,
        env: RoboThorEnvironment,
        task: Optional[PointNavTask],
        *args: Any,
        **kwargs: Any
    ) -> Any:

        agent_state = env.agent_state()
        agent_position = np.array([agent_state[k] for k in ["x", "y", "z"]])
        rotation_world_agent = self.quaternion_from_y_angle(
            agent_state["rotation"]["y"]
        )

        goal_position = np.array([task.task_info["target"][k] for k in ["x", "y", "z"]])

        return self._compute_pointgoal(
            agent_position, rotation_world_agent, goal_position
        )


class DepthSensorRoboThor(DepthSensor[RoboThorEnvironment, Task[RoboThorEnvironment]]):
    def __init__(
        self, config: Dict[str, Any], scale_first=False, *args: Any, **kwargs: Any
    ):
        def f(x, k, default):
            return x[k] if k in x else default

        # Backwards compatibility
        config["use_normalization"] = f(
            config, "use_normalization", f(config, "use_resnet_normalization", False)
        )

        super().__init__(config, scale_first, *args, **kwargs)

    def frame_from_env(self, env: RoboThorEnvironment) -> np.ndarray:
        return env.current_depth.copy()