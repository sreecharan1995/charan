import React from 'react';
import styles from '../../styles/Main.module.css';
import { useQuery } from 'react-query';
import useHttpClient from '../../hooks/useHttpClient';

export default function About(props: any) {
  const httpClient = useHttpClient();
  const {
    isLoading: dataIsLoading,
    error: infoError,
    data: infoData,
  } = useQuery('infoData', () => httpClient.get('/api/info'));

  return (
    <div className={styles.container}>
      <div>
        <h1>About</h1>
        <h2>Web app version</h2>
        <p>BUILD_ID: {props.webapp_build_id}</p>
        <p>BUILD_DATE: {props.webapp_build_date}</p>
        <p>BUILD_HASH: {props.webapp_build_hash}</p>
        <p>BUILD_LINK: {props.webapp_build_url}</p>
      </div>
      <div>
        <h2>Dependency service version</h2>
        <div>
          {dataIsLoading || status === 'loading' ? (
            <div>Loading...</div>
          ) : infoError ? (
            <div>An error has occurred</div>
          ) : (
            <div>
              <p>Build ID: {infoData.dependency_info.build_id}</p>
              <p>Build date: {infoData.dependency_info.build_date}</p>
              <p>Build hash: {infoData.dependency_info.build_hash}</p>
              <p>Build link: {infoData.dependency_info.build_link}</p>
            </div>
          )}
        </div>
      </div>
      <div>
        <h2>Rez service version</h2>
        <div>
          {dataIsLoading || status === 'loading' ? (
            <div>Loading...</div>
          ) : infoError ? (
            <div>An error has occurred</div>
          ) : (
            <div>
              <p>Build ID: {infoData.rez_info.build_id}</p>
              <p>Build date: {infoData.rez_info.build_date}</p>
              <p>Build hash: {infoData.rez_info.build_hash}</p>
              <p>Build link: {infoData.rez_info.build_link}</p>
            </div>
          )}
        </div>
      </div>
        <div>
            <h2>Level service version</h2>
            <div>
                {dataIsLoading || status === 'loading' ? (
                    <div>Loading...</div>
                ) : infoError ? (
                    <div>An error has occurred</div>
                ) : (
                    <div>
                        <p>Build ID: {infoData.level_info.build_id}</p>
                        <p>Build date: {infoData.level_info.build_date}</p>
                        <p>Build hash: {infoData.level_info.build_hash}</p>
                        <p>Build link: {infoData.level_info.build_link}</p>
                    </div>
                )}
            </div>
        </div>
        <div>
            <h2>Configs Service Version</h2>
            <div>
                {dataIsLoading || status === 'loading' ? (
                    <div>Loading...</div>
                ) : infoError ? (
                    <div>An error has occurred</div>
                ) : (
                    <div>
                        <p>Build ID: {infoData.configs_info.build_id}</p>
                        <p>Build date: {infoData.configs_info.build_date}</p>
                        <p>Build hash: {infoData.configs_info.build_hash}</p>
                        <p>Build link: {infoData.configs_info.build_link}</p>
                    </div>
                )}
            </div>
        </div>
        <div>
            <h2>Sourcing Service Version</h2>
            <div>
                {dataIsLoading || status === 'loading' ? (
                    <div>Loading...</div>
                ) : infoError ? (
                    <div>An error has occurred</div>
                ) : (
                    <div>
                        <p>Build ID: {infoData.sourcing_info.build_id}</p>
                        <p>Build date: {infoData.sourcing_info.build_date}</p>
                        <p>Build hash: {infoData.sourcing_info.build_hash}</p>
                        <p>Build link: {infoData.sourcing_info.build_link}</p>
                    </div>
                )}
            </div>
        </div>
        <div>
            <h2>Scheduler Service Version</h2>
            <div>
                {dataIsLoading || status === 'loading' ? (
                    <div>Loading...</div>
                ) : infoError ? (
                    <div>An error has occurred</div>
                ) : (
                    <div>
                        <p>Build ID: {infoData.scheduler_info.build_id}</p>
                        <p>Build date: {infoData.scheduler_info.build_date}</p>
                        <p>Build hash: {infoData.scheduler_info.build_hash}</p>
                        <p>Build link: {infoData.scheduler_info.build_link}</p>
                    </div>
                )}
            </div>
        </div>
    </div>
  );
}

export async function getServerSideProps() {
  return {
    props: {
      webapp_build_id: process.env.NEXT_PUBLIC_BUILD_ID,
      webapp_build_date: process.env.NEXT_PUBLIC_BUILD_DATE,
      webapp_build_hash: process.env.NEXT_PUBLIC_BUILD_HASH,
      webapp_build_url: process.env.NEXT_PUBLIC_BUILD_LINK,
    },
  };
}
