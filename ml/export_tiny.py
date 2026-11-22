from pathlib import Path
import numpy as np
import onnx
from onnx import helper, TensorProto, numpy_helper

rng = np.random.default_rng(0)
w1 = (rng.standard_normal((8, 3, 3, 3)) * 0.1).astype(np.float32)
w2 = (rng.standard_normal((3, 8, 3, 3)) * 0.1).astype(np.float32)

nodes = [
    helper.make_node("Conv", ["x", "w1"], ["h"], pads=[1, 1, 1, 1]),
    helper.make_node("Relu", ["h"], ["h2"]),
    helper.make_node("Conv", ["h2", "w2"], ["y"], pads=[1, 1, 1, 1]),
]
graph = helper.make_graph(
    nodes,
    "tiny",
    [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, 3, 256, 256])],
    [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 3, 256, 256])],
    initializer=[numpy_helper.from_array(w1, "w1"), numpy_helper.from_array(w2, "w2")],
)
model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
model.ir_version = 8  # older IR version = wider runtime compatibility
onnx.checker.check_model(model)

out = Path(__file__).resolve().parents[1] / "web" / "public" / "tiny.onnx"
out.parent.mkdir(parents=True, exist_ok=True)
onnx.save(model, out)
print("saved", out)