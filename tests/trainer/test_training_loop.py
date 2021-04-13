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

from pytorch_lightning import Trainer
from tests.helpers import BoringModel


def test_training_loop_hook_call_order(tmpdir):
    """Tests that hooks / methods called in the training loop are in the correct order as detailed in the docs:
    https://pytorch-lightning.readthedocs.io/en/latest/common/lightning_module.html#hooks"""

    class HookedModel(BoringModel):

        def __init__(self):
            super().__init__()
            self.called = []

        def on_epoch_start(self):
            self.called.append("on_epoch_start")
            super().on_epoch_start()

        def on_train_epoch_start(self):
            self.called.append("on_train_epoch_start")
            super().on_train_epoch_start()

        def on_train_batch_start(self, batch, batch_idx, dataloader_idx):
            self.called.append("on_train_batch_start")
            super().on_train_batch_start(batch, batch_idx, dataloader_idx)

        def training_step(self, batch, batch_idx):
            self.called.append("training_step")
            return super().training_step(batch, batch_idx)

        def on_before_zero_grad(self, optimizer):
            self.called.append("on_before_zero_grad")
            super().on_before_zero_grad(optimizer)

        def optimizer_zero_grad(self, epoch, batch_idx, optimizer, optimizer_idx):
            self.called.append("optimizer_zero_grad")
            super().optimizer_zero_grad(epoch, batch_idx, optimizer, optimizer_idx)

        def backward(self, loss, optimizer, optimizer_idx, *args, **kwargs):
            self.called.append("backward")
            super().backward(loss, optimizer, optimizer_idx, *args, **kwargs)

        def on_after_backward(self):
            self.called.append("on_after_backward")
            super().on_after_backward()

        def optimizer_step(
            self,
            epoch,
            batch_idx,
            optimizer,
            optimizer_idx,
            optimizer_closure,
            on_tpu,
            using_native_amp,
            using_lbfgs,
        ):
            super().optimizer_step(
                epoch, batch_idx, optimizer, optimizer_idx, optimizer_closure, on_tpu, using_native_amp, using_lbfgs
            )
            self.called.append("optimizer_step")  # append after as closure calls other methods

        def on_train_batch_end(self, outputs, batch, batch_idx, dataloader_idx):
            self.called.append("on_train_batch_end")
            super().on_train_batch_end(outputs, batch, batch_idx, dataloader_idx)

        def training_epoch_end(self, outputs):
            self.called.append("training_epoch_end")
            super().training_epoch_end(outputs)

        def on_train_epoch_end(self, outputs):
            self.called.append("on_train_epoch_end")
            super().on_train_epoch_end(outputs)

        def on_epoch_end(self):
            self.called.append("on_epoch_end")
            super().on_epoch_end()

    model = HookedModel()

    # fit model
    trainer = Trainer(
        default_root_dir=tmpdir,
        max_epochs=1,
        limit_val_batches=1,
        limit_train_batches=1,
        limit_test_batches=1,
        progress_bar_refresh_rate=0,
        weights_summary=None,
    )

    assert model.called == []

    trainer.fit(model)
    expected = [
        'on_epoch_start',  # validation
        'on_epoch_end',
        'on_epoch_start',  # training
        'on_train_epoch_start',
        'on_train_batch_start',
        'training_step',
        'on_before_zero_grad',
        'optimizer_zero_grad',
        'backward',
        'on_after_backward',
        'optimizer_step',
        'on_train_batch_end',
        'training_epoch_end',
        'on_train_epoch_end',
        'on_epoch_end',
        'on_epoch_start',  # validation
        'on_epoch_end'
    ]
    assert model.called == expected


def test_outputs_format(tmpdir):
    """Tests that outputs objects passed to model hooks and methods are consistent and in the correct format."""

    class HookedModel(BoringModel):

        def training_step(self, batch, batch_idx):
            self.log("foo", "bar")
            return super().training_step(batch, batch_idx)

        @staticmethod
        def _check_output(output):
            assert "loss" in output

            assert "foo" in output
            assert output["foo"] == "bar"

        def on_train_batch_end(self, outputs, batch, batch_idx, dataloader_idx):
            HookedModel._check_output(outputs)
            super().on_train_batch_end(outputs, batch, batch_idx, dataloader_idx)

        def training_epoch_end(self, outputs):
            assert len(outputs) == 2
            [HookedModel._check_output(output) for output in outputs]
            super().training_epoch_end(outputs)

        def on_train_epoch_end(self, outputs):
            assert len(outputs) == 2
            [HookedModel._check_output(output) for output in outputs]
            super().on_train_epoch_end(outputs)

    model = HookedModel()

    # fit model
    trainer = Trainer(
        default_root_dir=tmpdir,
        max_epochs=1,
        limit_val_batches=1,
        limit_train_batches=2,
        limit_test_batches=1,
        progress_bar_refresh_rate=0,
        weights_summary=None,
    )

    result = trainer.fit(model)
    assert result == 1, "Training did not complete"
