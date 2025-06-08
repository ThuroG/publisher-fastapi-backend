CREATE TABLE public.posts
(
    id serial,
    title character varying NOT NULL,
    content character varying NOT NULL,
    rating smallint,
    published boolean NOT NULL DEFAULT false,
    created_at timestamp with time zone default current_timestamp,
    PRIMARY KEY (id)
);

ALTER TABLE IF EXISTS public.posts
    OWNER to postgres;