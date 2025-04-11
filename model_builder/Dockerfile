FROM jupyter/minimal-notebook:612aa5710bf9

ARG GILLESPY3D_PIP_EDITABLE
ARG JUPYTER_CONFIG_DIR


USER root

WORKDIR /model_builder

RUN apt-get update && apt-get install -y zip

RUN chown jovyan:users /model_builder

USER jovyan

COPY --chown=jovyan:users requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=jovyan:users package.json /model_builder  

RUN npm install

COPY --chown=jovyan:users public_models/ /home/jovyan/Examples

COPY --chown=jovyan:users . /model_builder  

COPY --chown=jovyan:users /model_builder/dist/favicon.ico $JUPYTER_CONFIG_DIR/custom/favicon.ico

COPY --chown=jovyan:users custom.js $JUPYTER_CONFIG_DIR/custom/custom.js

COPY --chown=jovyan:users model_builder-logo.png $JUPYTER_CONFIG_DIR/custom/logo.png

COPY --chown=jovyan:users custom.css $JUPYTER_CONFIG_DIR/custom/custom.css

COPY --chown=jovyan:users jupyter_notebook_config.py $JUPYTER_CONFIG_DIR/jupyter_notebook_config.py

RUN pip install --no-cache-dir -e .

RUN rm -r /home/jovyan/work

RUN npm run webpack

WORKDIR /home/jovyan
