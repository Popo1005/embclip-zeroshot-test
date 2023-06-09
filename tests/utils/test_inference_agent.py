import torch

from allenact.utils.experiment_utils import set_seed
from allenact.utils.inference import InferenceAgent
from projects.babyai_baselines.experiments.go_to_obj.ppo import (
    PPOBabyAIGoToObjExperimentConfig,
)

expected_results = [
    {"ep_length": 64, "reward": 0.0, "success": 0.0},
    {"ep_length": 64, "reward": 0.0, "success": 0.0},
    {"ep_length": 64, "reward": 0.0, "success": 0.0},
    {"ep_length": 17, "reward": 0.7646153846153846, "success": 1.0},
    {"ep_length": 22, "reward": 0.6953846153846154, "success": 1.0},
    {"ep_length": 64, "reward": 0.0, "success": 0.0},
    {"ep_length": 64, "reward": 0.0, "success": 0.0},
    {"ep_length": 64, "reward": 0.0, "success": 0.0},
    {"ep_length": 64, "reward": 0.0, "success": 0.0},
    {"ep_length": 64, "reward": 0.0, "success": 0.0},
]


class TestInferenceAgent(object):
    def test_inference_agent_from_minigrid_config(self):
        set_seed(1)

        exp_config = PPOBabyAIGoToObjExperimentConfig()
        agent = InferenceAgent.from_experiment_config(
            exp_config=exp_config, device=torch.device("cpu"),
        )

        task_sampler = exp_config.make_sampler_fn(
            **exp_config.test_task_sampler_args(process_ind=0, total_processes=1)
        )

        for ind, expected_result in zip(range(10), expected_results):
            agent.reset()

            task = task_sampler.next_task()
            observations = task.get_observations()

            while not task.is_done():
                action = agent.act(observations=observations)
                observations = task.step(action).observation

            assert all(
                abs(v - expected_result[k]) < 1e-4
                for k, v in task.metrics().items()
                if k != "task_info"
            )


if __name__ == "__main__":
    TestInferenceAgent().test_inference_agent_from_minigrid_config()
