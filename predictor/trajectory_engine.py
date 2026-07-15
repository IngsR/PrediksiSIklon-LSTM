# ==========================================================
# predictor/trajectory_engine.py
# Main Prediction Pipeline
# ==========================================================

from predictor.loader import load_pipeline

from predictor.preprocessing import prepare_input

from predictor.inference import run_inference

from predictor.constraints import apply_constraints

from predictor.postprocessing import refine


class CyclonePredictor:

    def __init__(

        self,

        dataset="gab",

        window_size=8

    ):

        self.dataset = dataset

        self.window_size = window_size

        pipeline = load_pipeline(dataset)

        self.model = pipeline["model"]

        self.feature_scaler = pipeline["feature_scaler"]

        self.target_scaler = pipeline["target_scaler"]


    # ======================================================

    def preprocess(

        self,

        history

    ):

        return prepare_input(

            df=history,

            scaler=self.feature_scaler,

            window_size=self.window_size

        )


    # ======================================================

    def inference(

        self,

        sequence

    ):

        return run_inference(

            model=self.model,

            sequence=sequence,

            scaler_y=self.target_scaler

        )


    # ======================================================

    def refinement(

        self,

        history,

        prediction

    ):

        prediction = apply_constraints(

            history,

            prediction

        )

        prediction = refine(

            history,

            prediction

        )

        return prediction


    # ======================================================

    def predict(

        self,

        history

    ):

        sequence = self.preprocess(

            history

        )

        raw_prediction = self.inference(

            sequence

        )

        refined_prediction = self.refinement(

            history,

            raw_prediction

        )

        return {

            "raw_prediction": raw_prediction,

            "final_prediction": refined_prediction,

            "dataset": self.dataset,

            "window_size": self.window_size

        }