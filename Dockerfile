# parameters
ARG REPO_NAME="cuDUCK_DL"
ARG DESCRIPTION="This is a deep learning implementation of the self driving duckiebot"
ARG MAINTAINER="Cael Black, blackcael@gmail.com"
# pick an icon from: https://fontawesome.com/v4.7.0/icons/
ARG ICON="cube"

# ==================================================>
# ==> Do not change the code below this line
ARG ARCH=arm32v7
ARG DISTRO=daffy
ARG BASE_TAG=${DISTRO}-${ARCH}
ARG BASE_IMAGE=dt-core
ARG LAUNCHER=default

# define base image
FROM duckietown/${BASE_IMAGE}:${BASE_TAG} as BASE

# recall all arguments
ARG ARCH
ARG DISTRO
ARG REPO_NAME
ARG DESCRIPTION
ARG MAINTAINER
ARG ICON
ARG BASE_TAG
ARG BASE_IMAGE
ARG LAUNCHER

# check build arguments
RUN dt-build-env-check "${REPO_NAME}" "${MAINTAINER}" "${DESCRIPTION}"

# define/create repository path
ARG REPO_PATH="${CATKIN_WS_DIR}/src/${REPO_NAME}"
ARG LAUNCH_PATH="${LAUNCH_DIR}/${REPO_NAME}"
RUN mkdir -p "${REPO_PATH}"
RUN mkdir -p "${LAUNCH_PATH}"
WORKDIR "${REPO_PATH}"

# keep some arguments as environment variables
ENV DT_MODULE_TYPE "${REPO_NAME}"
ENV DT_MODULE_DESCRIPTION "${DESCRIPTION}"
ENV DT_MODULE_ICON "${ICON}"
ENV DT_MAINTAINER "${MAINTAINER}"
ENV DT_REPO_PATH "${REPO_PATH}"
ENV DT_LAUNCH_PATH "${LAUNCH_PATH}"
ENV DT_LAUNCHER "${LAUNCHER}"

# Temporary fix for expired ROS Key that prevents apt update -- Braden and Nelson
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F42ED6FBAB17C654

# install apt dependencies
COPY ./dependencies-apt.txt "${REPO_PATH}/"
RUN dt-apt-install ${REPO_PATH}/dependencies-apt.txt

# install python3 dependencies
COPY ./dependencies-py3.txt "${REPO_PATH}/"
RUN pip3 install -r ${REPO_PATH}/dependencies-py3.txt
RUN pip3 install --upgrade opencv_python

# copy the source code
COPY ./packages "${REPO_PATH}/packages"
RUN pip3 install --upgrade opencv_python

# build packages
RUN . /opt/ros/${ROS_DISTRO}/setup.sh && \
  catkin build \
    --workspace ${CATKIN_WS_DIR}/

# install launcher scripts
COPY ./launchers/. "${LAUNCH_PATH}/"
COPY ./launchers/default.sh "${LAUNCH_PATH}/"
RUN dt-install-launchers "${LAUNCH_PATH}"

# define default command
CMD ["bash", "-c", "dt-launcher-${DT_LAUNCHER}"]

# store module metadata
LABEL org.duckietown.label.module.type="${REPO_NAME}" \
    org.duckietown.label.module.description="${DESCRIPTION}" \
    org.duckietown.label.module.icon="${ICON}" \
    org.duckietown.label.architecture="${ARCH}" \
    org.duckietown.label.code.location="${REPO_PATH}" \
    org.duckietown.label.code.version.distro="${DISTRO}" \
    org.duckietown.label.base.image="${BASE_IMAGE}" \
    org.duckietown.label.base.tag="${BASE_TAG}" \
    org.duckietown.label.maintainer="${MAINTAINER}"
# <== Do not change the code above this line
# <==================================================

# Auto source the catkin_ws
RUN echo 'source /code/catkin_ws/devel/setup.bash' >> ~/.bashrc
# Default location when entering the docker container
WORKDIR /code/catkin_ws

# Startup gate for joystick/controller availability.
COPY ./launchers/wait_for_joystick.sh /usr/local/bin/wait_for_joystick.sh
RUN chmod +x /usr/local/bin/wait_for_joystick.sh
ENV WAIT_FOR_JOYSTICK=1
ENV WAIT_FOR_JOYSTICK_INTERVAL=1
ENV WAIT_FOR_JOYSTICK_TIMEOUT=0
ENV WAIT_FOR_JOYSTICK_PATTERN=/dev/input/js*

# Override default command so launch waits for joystick before starting.
CMD ["bash", "-lc", "/usr/local/bin/wait_for_joystick.sh dt-launcher-${DT_LAUNCHER}"]
