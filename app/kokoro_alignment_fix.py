"""Build-time workaround for XPU repeat/scatter indexing on longer utterances.

Construct the small duration alignment matrix on CPU, then copy to XPU.
All neural layers remain on the B50. Preserve the model's numerical algorithm.
"""

import pathlib
import site

path = pathlib.Path(site.getsitepackages()[0]) / "kokoro" / "model.py"
source = path.read_text()
changes = {
    "torch.repeat_interleave(torch.arange(input_ids.shape[1], device=self.device), pred_dur)": "torch.repeat_interleave(torch.arange(input_ids.shape[1]), pred_dur.cpu())",
    "torch.zeros((input_ids.shape[1], indices.shape[0]), device=self.device)": "torch.zeros((input_ids.shape[1], indices.shape[0]), device='cpu')",
}
for old, new in changes.items():
    assert source.count(old) == 1, "Kokoro source changed: review workaround"
    source = source.replace(old, new)
compile(source, str(path), "exec")
path.write_text(source)
print("Kokoro duration alignment CPU workaround applied; neural layers stay XPU")
