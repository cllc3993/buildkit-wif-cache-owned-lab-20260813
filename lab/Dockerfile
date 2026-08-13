FROM alpine:3.22 AS intermediate
WORKDIR /app
COPY . .
RUN test -f /app/gha-creds-lab.json

FROM alpine:3.22
COPY --from=intermediate /app/lab/public.txt /public.txt
