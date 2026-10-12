# syntax=docker/dockerfile:1
# ---------- Étape 1 : build du connecteur EDC depuis eclipse-edc/Samples ----------
FROM eclipse-temurin:17-jdk AS build

ARG EDC_SAMPLES_REF=main
ARG CONNECTOR_MODULE=transfer:transfer-00-prerequisites:connector

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git clone https://github.com/eclipse-edc/Samples.git . \
 && git checkout ${EDC_SAMPLES_REF}

RUN ./gradlew ${CONNECTOR_MODULE}:build -x test --no-daemon \
 && cp transfer/transfer-00-prerequisites/connector/build/libs/connector.jar /connector.jar

# ---------- Étape 2 : image d'exécution ----------
FROM eclipse-temurin:17-jre

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/* \
 && useradd -r -u 1001 edc

WORKDIR /app
COPY --from=build /connector.jar /app/connector.jar

USER edc
ENV EDC_FS_CONFIG=/config/connector.properties
EXPOSE 19193 19194 19291

ENTRYPOINT ["sh", "-c", "exec java -Dedc.fs.config=${EDC_FS_CONFIG} -jar /app/connector.jar"]