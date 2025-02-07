# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
from typing import Any, Sequence, Tuple

import torch.nn as nn
from torch.optim import Optimizer

from pytorch_lightning.plugins.precision.precision_plugin import PrecisionPlugin


class TPUHalfPrecisionPlugin(PrecisionPlugin):
    """Plugin that enables bfloats on TPUs"""

    precision: int = 16

    def connect(
        self,
        model: nn.Module,
        optimizers: Sequence[Optimizer],
        lr_schedulers: Sequence[Any],
    ) -> Tuple[nn.Module, Sequence[Optimizer], Sequence[Any]]:
        os.environ["XLA_USE_BF16"] = str(1)
        return super().connect(model=model, optimizers=optimizers, lr_schedulers=lr_schedulers)
